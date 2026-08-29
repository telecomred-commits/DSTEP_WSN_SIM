PROFILES={
 "custom":{},
 "open_field":{"channel_model":"free_space","path_loss_exponent":2.0,"shadow_sigma_db":1.0},
 "forest":{"channel_model":"log_normal","path_loss_exponent":3.0,"shadow_sigma_db":6.0},
 "urban":{"channel_model":"log_normal","path_loss_exponent":3.4,"shadow_sigma_db":7.0},
 "industrial":{"channel_model":"rayleigh","path_loss_exponent":3.2,"shadow_sigma_db":5.0},
 "open_water":{"channel_model":"rician","path_loss_exponent":2.0,"shadow_sigma_db":2.0,"rician_k_db":8.0}
}
def apply_profile(radio_cfg,environment_cfg=None):
    environment_cfg=environment_cfg or {"profile":"custom"}
    profile=environment_cfg.get("profile","custom")
    if profile not in PROFILES: raise ValueError(f"Unknown environment profile: {profile}")
    merged=dict(radio_cfg); merged.update(PROFILES[profile])
    for k,v in environment_cfg.items():
        if k!="profile": merged[k]=v
    merged["environment_profile"]=profile
    return merged
