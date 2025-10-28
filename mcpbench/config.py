import yaml, os

def load_config(path_or_dict):
    if isinstance(path_or_dict, dict):
        return path_or_dict
    with open(path_or_dict, 'r') as f:
        cfg = yaml.safe_load(f)
    cfg.setdefault('results_dir', os.getenv('RESULTS_DIR','results'))
    return cfg
