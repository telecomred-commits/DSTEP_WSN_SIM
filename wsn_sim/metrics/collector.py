import math

def _mean(xs):
    return sum(xs) / len(xs) if xs else None

def summarize(sim):
    nodes = sim.nodes
    total_energy = sum(n.total_energy for n in nodes)
    tx = sum(n.tx_count for n in nodes)
    rx = sum(n.rx_count for n in nodes)
    bytes_tx = sum(n.bytes_tx for n in nodes)

    tp = fp = fn = 0
    deadline_ok = 0
    actual_events = 0

    detection_delays = []
    pre_event_local_detections = 0
    confirmation_delays = []
    alert_delays = []
    lead_times = []

    origin_errors = []
    speed_errors = []
    eta_errors = []

    for n in nodes:
        true_arrival = sim.world.arrival_time(n.position)
        truth = true_arrival <= sim.duration
        pred = n.detected

        if truth and pred:
            tp += 1
        elif (not truth) and pred:
            fp += 1
        elif truth and (not pred):
            fn += 1

        if truth:
            actual_events += 1

            if n.first_detection_time is not None:
                dd = n.first_detection_time - true_arrival
                detection_delays.append(dd)
                if dd < 0:
                    pre_event_local_detections += 1

            if n.first_confirmation_time is not None:
                confirmation_delays.append(n.first_confirmation_time - true_arrival)

            if n.first_alert_time is not None:
                alert_delay = n.first_alert_time - true_arrival
                alert_delays.append(alert_delay)
                lead_times.append(true_arrival - n.first_alert_time)
                if n.first_alert_time <= true_arrival + sim.deadline_s:
                    deadline_ok += 1

        # Ground truth is used ONLY here, by evaluator metrics, never by D-STEP.
        if sim.policy_name == "dstep":
            if n.est_origin is not None:
                origin_errors.append(math.dist(n.est_origin, sim.world.origin))
            if n.est_speed is not None:
                speed_errors.append(abs(n.est_speed - sim.world.speed))
            if n.est_origin is not None and n.est_speed is not None and n.est_t0 is not None:
                pred_arrival = n.est_t0 + math.dist(n.position, n.est_origin) / max(n.est_speed, 1e-9)
                eta_errors.append(abs(pred_arrival - true_arrival))

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    dcr = deadline_ok / actual_events if actual_events else 0.0

    e_sense = sum(n.energy_sense for n in nodes)
    e_prep = sum(n.energy_preprocess for n in nodes)
    e_infer = sum(n.energy_infer for n in nodes)
    e_consensus = sum(n.energy_consensus for n in nodes)
    e_estimate = sum(n.energy_estimate for n in nodes)
    e_prediction = sum(n.energy_prediction for n in nodes)
    e_tx = sum(n.energy_tx for n in nodes)
    e_rx = sum(n.energy_rx for n in nodes)
    e_idle = sum(n.energy_idle for n in nodes)
    suppressed_tx = sum(n.suppressed_tx_count for n in nodes)

    tx_power_values = [n.tx_power_dbm for n in nodes]
    tx_power_hist = [p for n in nodes for p in n.tx_power_history]
    power_changes = sum(n.radio_power_changes for n in nodes)
    power_increases = sum(n.radio_power_increases for n in nodes)
    power_decreases = sum(n.radio_power_decreases for n in nodes)
    feedback_rssi = [n.last_feedback_rssi_dbm for n in nodes if n.last_feedback_rssi_dbm is not None]
    feedback_success = [n.last_feedback_success_rate for n in nodes if n.last_feedback_success_rate is not None]
    backoff_actions = sum(n.radio_backoff_actions for n in nodes)
    wait_actions = sum(n.radio_wait_actions for n in nodes)
    congestion_events = sum(n.radio_congestion_events for n in nodes)
    coverage_events = sum(n.radio_coverage_events for n in nodes)
    radio_channel_loss_events = sum(n.radio_channel_loss_events for n in nodes)

    return {
        "policy": sim.policy_name,
        "nodes": len(nodes),
        "tx_packets": tx,
        "rx_packets": rx,
        "bytes_tx": bytes_tx,
        "energy_mj": round(total_energy, 4),

        "energy_sense_mj": round(e_sense, 4),
        "energy_preprocess_mj": round(e_prep, 4),
        "energy_infer_mj": round(e_infer, 4),
        "energy_consensus_mj": round(e_consensus, 4),
        "energy_estimate_mj": round(e_estimate, 4),
        "energy_prediction_mj": round(e_prediction, 4),
        "energy_tx_mj": round(e_tx, 4),
        "energy_rx_mj": round(e_rx, 4),
        "energy_idle_mj": round(e_idle, 4),

        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "dcr": round(dcr, 4),

        "mean_detection_delay_s": round(_mean(detection_delays), 4) if detection_delays else None,
        "pre_event_local_detections": pre_event_local_detections,
        "mean_confirmation_delay_s": round(_mean(confirmation_delays), 4) if confirmation_delays else None,
        "mean_alert_delay_s": round(_mean(alert_delays), 4) if alert_delays else None,
        "mean_lead_time_s": round(_mean(lead_times), 4) if lead_times else None,

        "mean_origin_error_m": round(_mean(origin_errors), 4) if origin_errors else None,
        "mean_speed_error_m_s": round(_mean(speed_errors), 4) if speed_errors else None,
        "mean_eta_error_s": round(_mean(eta_errors), 4) if eta_errors else None,

        "collisions": sim.collisions,
        "channel_losses": sim.channel_losses,
        "below_sensitivity": getattr(sim, "below_sensitivity", 0),
        "suppressed_tx": suppressed_tx,
        "radio_control_mode": sim.cfg.get("radio_control", {}).get("mode", "fixed"),
        "mean_tx_power_dbm": round(_mean(tx_power_values), 4) if tx_power_values else None,
        "min_tx_power_dbm": round(min(tx_power_values), 4) if tx_power_values else None,
        "max_tx_power_dbm": round(max(tx_power_values), 4) if tx_power_values else None,
        "mean_power_history_dbm": round(_mean(tx_power_hist), 4) if tx_power_hist else None,
        "power_changes": power_changes,
        "power_increases": power_increases,
        "power_decreases": power_decreases,
        "mean_feedback_rssi_dbm": round(_mean(feedback_rssi), 4) if feedback_rssi else None,
        "mean_feedback_success_rate": round(_mean(feedback_success), 4) if feedback_success else None,
        "radio_backoff_actions": backoff_actions,
        "radio_wait_actions": wait_actions,
        "radio_congestion_events": congestion_events,
        "radio_coverage_events": coverage_events,
        "radio_channel_loss_events": radio_channel_loss_events,
    }
