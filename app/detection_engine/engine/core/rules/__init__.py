from .sqli import detect_sqli
from .xss import detect_xss
from .path_traversal import detect_path_traversal
from .brute_force import detect_brute_force
from .ssh_bruteforce import detect_ssh_brute_force

# List of all available rules
RULES = [
    detect_sqli,
    detect_xss,
    detect_path_traversal,
    detect_brute_force,
    detect_ssh_brute_force
]
