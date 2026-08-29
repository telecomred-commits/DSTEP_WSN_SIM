import math
import statistics
from .base import Policy

class DStepPolicy(Policy):
    name = "dstep"
    uses_local_inference = True

    def __init__(self, sim):
        super().__init__(sim)
        self.cfg = sim.cfg["dstep"]
        self.msg_seq = 0
        self.ablation_mode = getattr(sim, "ablation_mode", "full")
        self.ablation = sim.cfg.get("ablation", {}).get(self.ablation_mode, sim.cfg.get("ablation", {}).get("full", {}))

    # ---------- local information only ----------
    def _recent_messages(self, node):
        now = self.sim.engine.time
        window = self.cfg["estimate_memory_s"]
        out = []
        for m in node.messages_received[-self.cfg["message_memory"]:]:
            if m.get("type") not in ("evidence", "confirmed"):
                continue
            t_ref = m.get("detection_time")
            if t_ref is None:
                t_ref = m.get("time", now)
            if t_ref is None:
                t_ref = now
            if now - float(t_ref) <= window:
                out.append(m)
        return out

    def _neighbor_evidence(self, node):
        msgs = self._recent_messages(node)
        vals = [
            m.get("confidence", 0.0)
            for m in msgs
            if m.get("confidence", 0.0) >= self.cfg["neighbor_threshold"]
        ]
        return (sum(vals) / len(vals)) if vals else 0.0, len(vals)

    def _temporal_score(self, node):
        if node.first_detection_time is None:
            return 0.0
        dt = max(0.0, self.sim.engine.time - node.first_detection_time)
        return math.exp(-dt / max(self.cfg["temporal_tau_s"], 1e-9))

    def _spatial_score(self, node):
        msgs = self._recent_messages(node)
        scores = []
        for m in msgs:
            pos = m.get("position")
            if pos is None:
                continue
            d = math.dist(node.position, tuple(pos))
            scores.append(math.exp(-d / max(self.cfg["spatial_lambda_m"], 1e-9)))
        return sum(scores) / len(scores) if scores else 0.0

    def _belief(self, node, confidence):
        if not self.ablation.get("use_consensus", True):
            return confidence

        node.energy_consensus += self.sim.cfg["energy_mj"]["consensus"]
        neigh, _ = self._neighbor_evidence(node)
        temporal = self._temporal_score(node)
        spatial = self._spatial_score(node)
        w = self.cfg["belief_weights"]
        return (
            w["local"] * confidence
            + w["neighbor"] * neigh
            + w["temporal"] * temporal
            + w["spatial"] * spatial
        )

    # ---------- robust physical estimator ----------
    @staticmethod
    def _fit_time_distance(points, origin, min_speed, max_speed):
        distances = [math.dist((p[0], p[1]), origin) for p in points]
        times = [p[2] for p in points]
        if len(points) < 3:
            return None

        dmean = sum(distances) / len(distances)
        tmean = sum(times) / len(times)
        var_d = sum((d - dmean) ** 2 for d in distances)
        if var_d <= 1e-9:
            return None

        slope = sum((d - dmean) * (t - tmean) for d, t in zip(distances, times)) / var_d
        if slope <= 1e-6:
            return None

        speed = max(min_speed, min(max_speed, 1.0 / slope))
        t0 = tmean - dmean / speed
        residuals = [t - (t0 + d / speed) for d, t in zip(distances, times)]
        return speed, t0, residuals

    def _robust_candidate_fit(self, points, origin):
        rcfg = self.cfg["robust_estimator"]
        fit = self._fit_time_distance(
            points, origin,
            self.cfg["min_speed_m_s"],
            self.cfg["max_speed_m_s"]
        )
        if fit is None:
            return None

        speed, t0, residuals = fit
        abs_res = [abs(r) for r in residuals]
        med = statistics.median(abs_res) if abs_res else 0.0
        mad = statistics.median([abs(x - med) for x in abs_res]) if abs_res else 0.0
        threshold = max(0.05, med + rcfg["mad_scale"] * max(mad, 1e-6))

        indexed = list(zip(points, residuals))
        inliers = [p for p, r in indexed if abs(r) <= threshold]

        # Additional trimming for resilience to early false detections.
        ntrim = int(len(points) * rcfg["trim_fraction"])
        if ntrim > 0 and len(points) - ntrim >= rcfg["min_inliers"]:
            ranked = sorted(indexed, key=lambda pr: abs(pr[1]))
            inliers = [p for p, _ in ranked[:len(points)-ntrim]]

        if len(inliers) < rcfg["min_inliers"]:
            return None

        refit = self._fit_time_distance(
            inliers, origin,
            self.cfg["min_speed_m_s"],
            self.cfg["max_speed_m_s"]
        )
        if refit is None:
            return None

        speed, t0, residuals = refit
        score = statistics.median([abs(r) for r in residuals]) if residuals else 1e9
        return {
            "origin": origin,
            "speed": speed,
            "t0": t0,
            "residual_score": score,
            "inliers": len(inliers),
        }

    def _estimate_event(self, node):
        if not self.ablation.get("use_estimation", True):
            node.est_origin = None
            node.est_t0 = None
            node.est_speed = None
            node.est_direction = None
            node.est_eta = None
            node.estimate_points = 0
            return None

        node.energy_estimate += self.sim.cfg["energy_mj"]["estimate"]

        points = []
        if node.first_detection_time is not None:
            points.append((
                node.position[0], node.position[1],
                node.first_detection_time,
                max(node.local_confidence, 0.05)
            ))

        seen = {node.node_id}
        for m in self._recent_messages(node):
            sid = m.get("source")
            pos = m.get("position")
            td = m.get("detection_time")
            if sid in seen or pos is None or td is None:
                continue
            seen.add(sid)
            points.append((
                float(pos[0]), float(pos[1]), float(td),
                max(float(m.get("confidence", 0.05)), 0.05)
            ))

        node.estimate_points = len(points)
        if len(points) < self.cfg["min_points_estimate"]:
            return None

        # Candidate origins: earliest detections + weighted early centroid.
        points_sorted = sorted(points, key=lambda p: p[2])
        maxc = min(self.cfg["robust_estimator"]["max_candidates"], len(points_sorted))
        candidates = [(p[0], p[1]) for p in points_sorted[:maxc]]

        tmin = points_sorted[0][2]
        tau = max(self.cfg["temporal_tau_s"], 0.5)
        weights = [max(1e-6, p[3] * math.exp(-(p[2] - tmin) / tau)) for p in points]
        sw = sum(weights)
        centroid = (
            sum(w*p[0] for w, p in zip(weights, points))/sw,
            sum(w*p[1] for w, p in zip(weights, points))/sw
        )
        candidates.append(centroid)

        fits = []
        for origin in candidates:
            f = self._robust_candidate_fit(points, origin)
            if f is not None:
                fits.append(f)
        if not fits:
            return None

        best = min(fits, key=lambda x: x["residual_score"])
        ox, oy = best["origin"]
        speed, t0 = best["speed"], best["t0"]

        # Direction estimate from origin toward later/high-confidence detections.
        recent = sorted(points, key=lambda p: p[2])[-max(3, len(points)//2):]
        wsum = sum(p[3] for p in recent)
        rx = sum(p[0]*p[3] for p in recent)/wsum
        ry = sum(p[1]*p[3] for p in recent)/wsum
        dx, dy = rx-ox, ry-oy
        norm = math.hypot(dx, dy)
        direction = (dx/norm, dy/norm) if norm > 1e-9 else None

        # Smooth local estimates.
        a = self.cfg["estimate_smoothing"]
        if node.est_origin is not None:
            ox = a*ox + (1-a)*node.est_origin[0]
            oy = a*oy + (1-a)*node.est_origin[1]
        if node.est_speed is not None:
            speed = a*speed + (1-a)*node.est_speed
        if node.est_t0 is not None:
            t0 = a*t0 + (1-a)*node.est_t0

        node.est_origin = (ox, oy)
        node.est_speed = speed
        node.est_t0 = t0
        node.est_direction = direction

        return {
            "origin": node.est_origin,
            "speed": node.est_speed,
            "t0": node.est_t0,
            "direction": node.est_direction,
            "points": node.estimate_points,
            "inliers": best["inliers"],
            "residual_score": best["residual_score"],
        }

    def _predict_eta(self, node, estimate):
        if not self.ablation.get("use_prediction", True):
            node.est_eta = None
            return None

        node.energy_prediction += self.sim.cfg["energy_mj"]["prediction"]
        if not estimate or estimate.get("origin") is None or estimate.get("speed") is None:
            node.est_eta = None
            return None
        d = math.dist(node.position, tuple(estimate["origin"]))
        predicted_arrival = estimate["t0"] + d / max(estimate["speed"], 1e-9)
        node.est_eta = predicted_arrival - self.sim.engine.time
        return node.est_eta

    # ---------- VoI ----------
    def _voi(self, node, confidence, belief, eta):
        msgs = self._recent_messages(node)
        prev_vals = [m.get("confidence", 0.0) for m in msgs]
        prev = (sum(prev_vals)/len(prev_vals)) if prev_vals else 0.0

        novelty = abs(confidence-prev)
        uncertainty = max(0.0, 1.0-abs(0.5-belief)*2.0)
        contradiction = abs(confidence-prev) if msgs else 0.0
        if eta is None:
            timeliness = 0.0
        elif eta <= 0:
            timeliness = 1.0
        else:
            timeliness = max(0.0, 1.0-eta/max(self.sim.deadline_s,1e-9))
        spatial = self._spatial_score(node)

        if not self.ablation.get("use_voi", True):
            # Neutral fixed utility: forwarding is then governed by
            # density/direction/suppression only.
            return 1.0

        w = self.cfg["voi_weights"]
        return max(0.0, min(1.0,
            w["novelty"]*novelty
            + w["uncertainty"]*uncertainty
            + w["contradiction"]*contradiction
            + w["timeliness"]*timeliness
            + w["spatial"]*spatial
        ))

    # ---------- density-aware forwarding ----------
    def _degree(self, node):
        return len(self.sim.neighbors(node))

    def _density_factor(self, node):
        dcfg = self.cfg["density_forwarding"]
        if (not dcfg.get("enabled", True)) or (not self.ablation.get("use_density", True)):
            return 1.0
        degree = self._degree(node)
        ref = max(1e-9, dcfg["reference_degree"])
        factor = (ref / max(ref, degree)) ** dcfg["density_exponent"]
        return max(dcfg["min_density_factor"], min(1.0, factor))

    def _directional_score(self, node, message):
        direction = node.est_direction
        if direction is None:
            return 0.5
        src_pos = tuple(message.get("position", node.position))
        vx = node.position[0]-src_pos[0]
        vy = node.position[1]-src_pos[1]
        nv = math.hypot(vx,vy)
        if nv <= 1e-9:
            return 0.0
        return max(0.0, (vx*direction[0]+vy*direction[1])/nv)

    def _equivalent_seen(self, node, message):
        if not self.ablation.get("use_suppression", True):
            return False
        dcfg = self.cfg["density_forwarding"]
        now = self.sim.engine.time
        conf = message.get("confidence", 0.0)
        event_type = message.get("type")

        # prune
        node.suppression_memory = [
            x for x in node.suppression_memory
            if now - x["time"] <= dcfg["equivalence_time_s"]
        ]

        for x in node.suppression_memory:
            if x["type"] != event_type:
                continue
            if abs(x["confidence"] - conf) <= dcfg["equivalence_confidence_delta"]:
                return True
        return False

    def _remember_equivalent(self, node, message):
        node.suppression_memory.append({
            "time": self.sim.engine.time,
            "type": message.get("type"),
            "confidence": message.get("confidence", 0.0)
        })

    def _schedule_forward(self, node, message, score, estimate):
        dcfg = self.cfg["density_forwarding"]

        if self._equivalent_seen(node, message):
            node.suppressed_tx_count += 1
            return

        density = self._density_factor(node)
        effective_score = score * density
        if effective_score < self.cfg["forward_threshold"]:
            node.suppressed_tx_count += 1
            return

        # Better candidates wait less; dense neighborhoods wait more.
        if self.ablation.get("use_backoff", True):
            normalized = max(0.0, min(1.0, effective_score))
            backoff = dcfg["backoff_base_s"] + (1.0-normalized) * dcfg["backoff_max_s"]
            backoff /= max(density, 0.15)
        else:
            backoff = 0.0

        node.pending_forward_token += 1
        token = node.pending_forward_token

        fwd = dict(message)
        fwd["ttl"] = max(0, message.get("ttl", 0)-1)
        fwd["time"] = self.sim.engine.time + backoff
        if estimate is not None:
            fwd["estimate"] = estimate

        self.sim.engine.schedule(
            self.sim.engine.time + backoff,
            self._execute_forward,
            node, fwd, token
        )

    def _execute_forward(self, node, message, token):
        if token != node.pending_forward_token:
            node.suppressed_tx_count += 1
            return
        if message.get("ttl", 0) <= 0:
            node.suppressed_tx_count += 1
            return
        if self._equivalent_seen(node, message):
            node.suppressed_tx_count += 1
            return

        self._remember_equivalent(node, message)
        self.sim.broadcast(node, message)

    # ---------- messaging ----------
    def _make_msg_id(self, node):
        self.msg_seq += 1
        return f"{node.node_id}:{self.msg_seq}"

    def _send(self, node, confidence, belief, estimate, ttl=None, msg_type="evidence"):
        if ttl is None:
            ttl = self.cfg["ttl"]
        msg = {
            "msg_id": self._make_msg_id(node),
            "type": msg_type,
            "source": node.node_id,
            "position": node.position,
            "confidence": confidence,
            "belief": belief,
            "time": self.sim.engine.time,
            "detection_time": node.first_detection_time,
            "ttl": ttl,
            "estimate": estimate,
        }
        node.seen_messages.add(msg["msg_id"])
        self._remember_equivalent(node, msg)
        self.sim.broadcast(node, msg)

    # ---------- state machine ----------
    def on_sample(self, node, value, confidence):
        node.local_confidence = confidence

        if node.state == "NORMAL" and confidence >= self.cfg["local_threshold"]:
            node.state = "SUSPECT"

        belief = self._belief(node, confidence)
        node.global_belief = belief
        _, confirmations = self._neighbor_evidence(node)

        estimate = self._estimate_event(node)
        eta = self._predict_eta(node, estimate)
        voi = self._voi(node, confidence, belief, eta)

        if node.state == "SUSPECT":
            node.state = "VERIFY"
            if voi >= self.cfg["voi_threshold"]:
                self._send(node, confidence, belief, estimate)

        if node.state == "VERIFY":
            if belief >= self.cfg["confirm_threshold"] and confirmations >= self.cfg["min_confirmations"]:
                node.state = "CONFIRMED"
                node.confirmed = True
                if node.first_confirmation_time is None:
                    node.first_confirmation_time = self.sim.engine.time
                if node.first_alert_time is None:
                    node.first_alert_time = self.sim.engine.time
                estimate = self._estimate_event(node)
                self._predict_eta(node, estimate)
                self._send(node, confidence, belief, estimate, msg_type="confirmed")
                node.state = "PROPAGATE"

        if confidence < self.cfg["local_threshold"]*0.65 and node.state in ("SUSPECT","VERIFY"):
            node.state = "NORMAL"

    def on_receive(self, node, message):
        msg_id = message.get("msg_id")
        if msg_id and msg_id in node.seen_messages:
            return
        if msg_id:
            node.seen_messages.add(msg_id)

        ttl = message.get("ttl", 0)
        if ttl <= 0:
            return

        # A received equivalent message suppresses a pending redundant forward.
        if self._equivalent_seen(node, message):
            node.pending_forward_token += 1
        self._remember_equivalent(node, message)

        estimate = self._estimate_event(node)

        # Fall back to neighbor estimate only if local estimate not yet available.
        if estimate is None and message.get("estimate"):
            estimate = message["estimate"]
            if estimate.get("origin") is not None:
                node.est_origin = tuple(estimate["origin"])
            node.est_speed = estimate.get("speed")
            node.est_t0 = estimate.get("t0")
            if estimate.get("direction") is not None:
                node.est_direction = tuple(estimate["direction"])

        eta = self._predict_eta(node, estimate)
        conf = max(node.local_confidence, message.get("confidence", 0.0))
        belief = max(node.global_belief, message.get("belief", 0.0))
        voi = self._voi(node, conf, belief, eta)
        directional = self._directional_score(node, message)

        score = (
            self.cfg["voi_weight"]*voi
            + self.cfg["directional_weight"]*directional
        )

        if message.get("type") == "confirmed" and node.first_alert_time is None:
            node.first_alert_time = self.sim.engine.time

        self._schedule_forward(node, message, score, estimate)
