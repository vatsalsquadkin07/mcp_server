# mcp_classifier.py
# N-gram + TF-IDF Classifier with Command Validation

import re
from typing import Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from mcp_data import TRAINING_COMMANDS, LABELS


class MCPClassifier:
    """
    Multi-class classifier for command destructiveness using N-gram + TF-IDF.
    Includes command validation to detect if input is a valid CLI command.
    
    Pipeline:
    command → validate_command → tokenizer → n-gram generation (1-3) 
    → TF-IDF vectorization → LogisticRegression → risk classification
    """
    
    # Common CLI command keywords across ecosystems
    CLI_KEYWORDS = {
        # File operations
        'ls', 'cd', 'pwd', 'mkdir', 'touch', 'cp', 'mv', 'rm', 'cat', 'grep',
        'find', 'tar', 'zip', 'unzip', 'chmod', 'chown', 'chgrp',
        
        # System commands
        'echo', 'sed', 'awk', 'cut', 'sort', 'uniq', 'head', 'tail', 'wc',
        'top', 'ps', 'kill', 'killall', 'systemctl', 'service', 'reboot',
        'shutdown', 'halt', 'poweroff', 'sudo', 'su',
        
        # Git commands
        'git', 'svn', 'hg', 'mercurial',
        
        # Docker commands
        'docker', 'docker-compose', 'podman',
        
        # Kubernetes commands
        'kubectl', 'helm', 'oc',
        
        # Cloud CLIs
        'aws', 'gcloud', 'az', 'ibmcloud', 'gsutil',
        
        # Package managers
        'npm', 'yarn', 'pip', 'pip3', 'apt', 'apt-get', 'yum', 'dnf',
        'pacman', 'brew', 'composer', 'cargo', 'go', 'make', 'gradle',
        'maven', 'pnpm',
        
        # Database commands
        'mysql', 'psql', 'mongo', 'redis-cli', 'sqlplus', 'sqlite3',
        
        # Terraform
        'terraform', 'tf',
        
        # Other tools
        'node', 'python', 'java', 'ruby', 'perl', 'php', 'gcc', 'g++',
        'clang', 'curl', 'wget', 'ssh', 'scp', 'rsync', 'ftp', 'telnet',
        'nmap', 'ping', 'traceroute', 'netstat', 'ifconfig', 'ip',
        'iptables', 'ufw', 'firewall-cmd', 'vi', 'vim', 'nano', 'emacs',
        'less', 'more', 'watch', 'screen', 'tmux', 'cron', 'at',
        'df', 'du', 'free', 'uptime', 'who', 'whoami', 'hostname','vite',
        'webpack', 'tsc'

        # networking
        'curl', 'wget', 'dig', 'nslookup'

        # linux tools
        'journalctl', 'mount', 'umount',
        'lsblk', 'blkid', 'fdisk',

        # CI/CD tools
        'ansible', 'ansible-playbook', 'helmfile',
    }
    
    # SQL keywords
    SQL_KEYWORDS = {
        'select', 'insert', 'update', 'delete', 'drop', 'create', 'alter',
        'truncate', 'grant', 'revoke', 'from', 'where', 'join', 'union',
        'order', 'group', 'having', 'limit', 'offset', 'partition','table', 
        'database', 'index', 'view', 'constraint', 'schema', 'cascade', 'replace',
        'distinct', 'exists'
    }
    
    # Flags/options patterns (things that look like command options)
    OPTION_PATTERNS = [
        r'^-[a-zA-Z]$',           # Short option: -h, -v, -f
        r'^--[a-zA-Z\-]+$',       # Long option: --help, --force
        r'^-[a-zA-Z]+$',          # Combined short: -rfv
        r'^/[a-zA-Z]',            # Windows: /C, /D
    ]
    
    def __init__(self):
        """Initialize and train the classifier."""
        # Extract commands and labels
        self.commands, self.labels = zip(*TRAINING_COMMANDS)
        self.commands = list(self.commands)
        self.labels = list(self.labels)
        
        # Initialize TF-IDF vectorizer with N-gram support (1-3 grams)
        self.vectorizer = TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 4),  # Unigrams, bigrams, trigrams
            token_pattern=r"[a-zA-Z0-9_\-./*;]+", # CLI-specific tokens
            lowercase=True,
            stop_words=None,
            max_features=5000,
            min_df=1
        )
        
        # Initialize LogisticRegression classifier
        self.model = LogisticRegression(
            max_iter=300,
            class_weight='balanced',
            random_state=42,
            C=1.5
        )
        
        # Train the model
        self._fit()
    
    def _fit(self):
        """Fit the TF-IDF vectorizer and classifier."""
        X = self.vectorizer.fit_transform(self.commands)
        y = [LABELS.index(lbl) for lbl in self.labels]
        self.model.fit(X, y)
    
    def is_valid_command(self, command: str) -> Tuple[bool, str]:
        """
        Validate if input looks like a real CLI command.
        
        Args:
            command: Input string to validate
            
        Returns:
            Tuple of (is_valid, reason)
            - is_valid: True if looks like a command
            - reason: Explanation if invalid
        """
        command = command.strip().lower()
        
        # Check if empty
        if not command:
            return False, "Empty command"
        
        # Check if too short (less than 2 characters)
        if len(command) < 2:
            return False, "Command too short"
        
        # Check if contains only special characters (like "!@#$%")
        if not re.search(r'[a-zA-Z0-9]', command):
            return False, "No alphanumeric characters found"
        
        # Extract first word (the actual command)
        first_word = command.split()[0].strip()
        
        # Remove path separators to get the command name
        command_name = first_word.split('/')[-1].split('\\')[-1]
        
        # Remove common path/file indicators
        command_name = command_name.lstrip('./~')
        
        # Remove file extensions to get command
        command_base = command_name.split('.')[0]
        
        # Check if first word is a known CLI keyword
        if command_base in self.CLI_KEYWORDS:
            return True, "Valid CLI command"
        
        # Check if it looks like SQL
        tokens = command.split()
        if tokens and tokens[0].lower() in self.SQL_KEYWORDS:
            return True, "Valid SQL command"
        
        # Check if it matches common option patterns (indicates it's part of a command)
        if re.match(r'^-|^--', first_word):
            return False, "Only flags/options provided, no command"
        
        # Check if contains common CLI separators (pipes, redirects, etc.)
        if any(sep in command for sep in ['|', '>', '<', ';', '&&', '||', '&']):
            return True, "Valid command pipeline/chain"
        
        # Check if contains file paths (/, \, or ./)
        if any(sep in command for sep in ['/', '\\', './']):
            return True, "Contains file paths (likely valid)"
        
        # Check if looks like a multi-word command (git, kubectl, aws, etc.)
        if len(tokens) >= 2:
            if command_base in ['git', 'kubectl', 'docker', 'aws', 'gcloud', 'terraform']:
                return True, "Valid multi-word command"
            
        if command.startswith("sudo "):
            command = command[5:]
        
        # If none of the above, it's likely random text
        return False, "Does not appear to be a valid CLI command"
    
    def tokenize(self, command: str) -> list:
        """
        Tokenize a command into individual tokens.
        
        Args:
            command: CLI command string
            
        Returns:
            List of tokens
        """
        tokens = re.findall(r"[a-zA-Z0-9_\-./]+", command.lower())
        return tokens
    
    def predict(self, command: str) -> dict:
        """
        Predict the destructiveness risk of a command.
        Includes validation to check if input is actually a command.
        
        Args:
            command: CLI command string
            
        Returns:
            Dict with 'command', 'risk', 'confidence', 'is_valid', 'reason'
        """
        original_command = command
        command = command.strip()
        command = command.lower()
        command = command.replace(";", "")
        
        # Validate if it's a real command
        is_valid, reason = self.is_valid_command(command)
        
        # If not a valid command, return NO_COMMAND status
        if not is_valid:
            return {
                "command": original_command,
                "risk": "NO_COMMAND",
                "confidence": 0.0,
                "is_valid": False,
                "reason": reason
            }
        
        # If valid, proceed with risk classification
        try:
            X = self.vectorizer.transform([command])
            probs = self.model.predict_proba(X)[0]
            pred_idx = probs.argmax()
            risk = LABELS[pred_idx]
            confidence = float(probs[pred_idx])
            
            return {
                "command": original_command,
                "risk": risk,
                "confidence": round(confidence, 4),
                "is_valid": True,
                "reason": "Valid command - risk analyzed"
            }
        except Exception as e:
            return {
                "command": original_command,
                "risk": "ERROR",
                "confidence": 0.0,
                "is_valid": False,
                "reason": f"Error during classification: {str(e)}"
            }
    
    def predict_batch(self, commands: list) -> list:
        """Predict risk for multiple commands."""
        results = []
        for cmd in commands:
            result = self.predict(cmd)
            results.append(result)
        return results


# Singleton instance – model loads once at startup
mcp_classifier = MCPClassifier()