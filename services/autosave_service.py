#!/usr/bin/env python3
"""
Pokemon TCG Tracker - Auto-Save Service
Handles automatic saving of user data to a separate Python file.
This ensures data persistence across app updates and Git operations.
"""

import json
import os
import shutil
import importlib.util
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class AutoSaveService:
    """
    Service for auto-saving user data to a separate Python file.
    
    The data is saved to a Python file (user_data.py) which is:
    - Git-ignored to keep personal data private
    - Preserved during app updates
    - Easy to backup and restore
    - Human-readable for debugging
    """
    
    def __init__(self, data_file_path: str = "data/user_data.py"):
        """Initialize the auto-save service."""
        self.data_file_path = data_file_path
        self.backup_dir = os.path.join(os.path.dirname(data_file_path), 'backups')
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.data_file_path), exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Initialize data file if it doesn't exist
        self.ensure_data_file_exists()
        
        logger.info(f"🔧 AutoSave initialized: {self.data_file_path}")
    
    def ensure_data_file_exists(self):
        """Create the data file if it doesn't exist."""
        if not os.path.exists(self.data_file_path):
            logger.info(f"📁 Creating new data file: {self.data_file_path}")
            self.create_empty_data_file()
        else:
            logger.info(f"📁 Using existing data file: {self.data_file_path}")
    
    def create_empty_data_file(self):
        """Create an empty data file with default structure."""
        initial_data = '''#!/usr/bin/env python3
"""
Pokemon TCG Tracker - User Data
AUTO-GENERATED FILE - DO NOT EDIT MANUALLY

This file contains your Pokemon TCG match data and is automatically
managed by the Pokemon TCG Tracker application.

🔒 This file is git-ignored to keep your personal data private
💾 Data is automatically saved every 30 seconds
📊 Contains: matches, decks, deck history, and settings

Last updated: {timestamp}
"""

from datetime import datetime

# ==================================================================================
# MATCH DATA
# ==================================================================================

# Your match history data
MATCHES = []

# ==================================================================================
# DECK DATA
# ==================================================================================

# Your deck configurations
DECKS = {{
    "Pikachu ex": [
        {{"name": "Pikachu ex", "count": 3, "type": "Pokemon"}},
        {{"name": "Raichu", "count": 2, "type": "Pokemon"}},
        {{"name": "Professor's Research", "count": 4, "type": "Trainer"}},
        {{"name": "Ultra Ball", "count": 4, "type": "Trainer"}},
        {{"name": "Electric Energy", "count": 12, "type": "Energy"}}
    ],
    "Charizard ex": [
        {{"name": "Charizard ex", "count": 3, "type": "Pokemon"}},
        {{"name": "Charmander", "count": 4, "type": "Pokemon"}},
        {{"name": "Arcanine ex", "count": 2, "type": "Pokemon"}},
        {{"name": "Professor's Research", "count": 4, "type": "Trainer"}},
        {{"name": "Fire Energy", "count": 10, "type": "Energy"}}
    ]
}}

# ==================================================================================
# DECK HISTORY
# ==================================================================================

# Track of deck modifications over time
DECK_HISTORY = [
    {{
        "date": "{today}",
        "change": "Initial Setup",
        "cards": "Created starter decks",
        "reason": "Application initialization"
    }}
]

# ==================================================================================
# SETTINGS
# ==================================================================================

# Currently selected deck
CURRENT_DECK = "Pikachu ex"

# Metadata
LAST_SAVE = "{timestamp}"
DATA_VERSION = "2.1.0"
TOTAL_MATCHES = 0
TOTAL_WINS = 0

# ==================================================================================
# DATA VALIDATION
# ==================================================================================

def validate_data():
    """Validate data integrity."""
    try:
        assert isinstance(MATCHES, list), "MATCHES must be a list"
        assert isinstance(DECKS, dict), "DECKS must be a dictionary"
        assert isinstance(DECK_HISTORY, list), "DECK_HISTORY must be a list"
        assert isinstance(CURRENT_DECK, str), "CURRENT_DECK must be a string"
        return True
    except AssertionError as e:
        print(f"❌ Data validation failed: {{e}}")
        return False

# Auto-validate on import
if __name__ == "__main__":
    if validate_data():
        print("✅ Data file is valid")
        print(f"📊 Matches: {{len(MATCHES)}}")
        print(f"🃏 Decks: {{len(DECKS)}}")
        print(f"📚 History entries: {{len(DECK_HISTORY)}}")
        print(f"🎯 Current deck: {{CURRENT_DECK}}")
    else:
        print("❌ Data file validation failed")
'''.format(
            timestamp=datetime.now().isoformat(),
            today=datetime.now().strftime('%Y-%m-%d')
        )
        
        os.makedirs(os.path.dirname(self.data_file_path), exist_ok=True)
        with open(self.data_file_path, 'w', encoding='utf-8') as f:
            f.write(initial_data)
        
        logger.info(f"✅ Created empty data file with starter data")
    
    def create_backup(self) -> str:
        """Create a backup of the current data file."""
        if not os.path.exists(self.data_file_path):
            logger.warning("⚠️ No data file to backup")
            return None
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"user_data_backup_{timestamp}.py"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        try:
            shutil.copy2(self.data_file_path, backup_path)
            logger.info(f"💾 Created backup: {backup_filename}")
            
            # Clean up old backups (keep only last 7)
            self.cleanup_old_backups()
            
            return backup_path
        except Exception as e:
            logger.error(f"❌ Failed to create backup: {e}")
            return None
    
    def cleanup_old_backups(self, max_backups: int = 7):
        """Remove old backup files, keeping only the most recent ones."""
        try:
            backup_files = [
                f for f in os.listdir(self.backup_dir)
                if f.startswith('user_data_backup_') and f.endswith('.py')
            ]
            
            # Sort by creation time (newest first)
            backup_files.sort(key=lambda f: os.path.getctime(
                os.path.join(self.backup_dir, f)
            ), reverse=True)
            
            # Remove excess backups
            for old_backup in backup_files[max_backups:]:
                old_backup_path = os.path.join(self.backup_dir, old_backup)
                os.remove(old_backup_path)
                logger.info(f"🗑️ Removed old backup: {old_backup}")
                
        except Exception as e:
            logger.error(f"❌ Failed to cleanup old backups: {e}")
    
    def save_data(self, matches: List[Dict], decks: Dict, deck_history: List, current_deck: str):
        """Save data to the user data file."""
        try:
            # Create backup before saving
            self.create_backup()
            
            # Calculate statistics
            total_matches = len(matches)
            total_wins = len([m for m in matches if m.get('result') == 'Win'])
            win_rate = (total_wins / total_matches * 100) if total_matches > 0 else 0
            
            # Generate the Python data file content
            data_content = '''#!/usr/bin/env python3
"""
Pokemon TCG Tracker - User Data
AUTO-GENERATED FILE - DO NOT EDIT MANUALLY

This file contains your Pokemon TCG match data and is automatically
managed by the Pokemon TCG Tracker application.

🔒 This file is git-ignored to keep your personal data private
💾 Data is automatically saved every 30 seconds
📊 Contains: matches, decks, deck history, and settings

Statistics:
- Total Matches: {total_matches}
- Total Wins: {total_wins}
- Win Rate: {win_rate:.1f}%
- Active Decks: {active_decks}

Last updated: {timestamp}
"""

from datetime import datetime

# ==================================================================================
# MATCH DATA
# ==================================================================================

# Your match history data
MATCHES = {matches_data}

# ==================================================================================
# DECK DATA
# ==================================================================================

# Your deck configurations
DECKS = {decks_data}

# ==================================================================================
# DECK HISTORY
# ==================================================================================

# Track of deck modifications over time
DECK_HISTORY = {history_data}

# ==================================================================================
# SETTINGS
# ==================================================================================

# Currently selected deck
CURRENT_DECK = "{current_deck}"

# Metadata
LAST_SAVE = "{timestamp}"
DATA_VERSION = "2.1.0"
TOTAL_MATCHES = {total_matches}
TOTAL_WINS = {total_wins}
WIN_RATE = {win_rate:.1f}

# ==================================================================================
# DATA VALIDATION
# ==================================================================================

def validate_data():
    """Validate data integrity."""
    try:
        assert isinstance(MATCHES, list), "MATCHES must be a list"
        assert isinstance(DECKS, dict), "DECKS must be a dictionary"
        assert isinstance(DECK_HISTORY, list), "DECK_HISTORY must be a list"
        assert isinstance(CURRENT_DECK, str), "CURRENT_DECK must be a string"
        
        # Validate match structure
        for i, match in enumerate(MATCHES):
            assert isinstance(match, dict), f"Match {{i}} must be a dictionary"
            required_fields = ['date', 'result', 'myDeck', 'opponentDeck']
            for field in required_fields:
                assert field in match, f"Match {{i}} missing required field: {{field}}"
        
        # Validate deck structure
        for deck_name, cards in DECKS.items():
            assert isinstance(cards, list), f"Deck '{{deck_name}}' must be a list"
            for card in cards:
                assert isinstance(card, dict), f"Card in deck '{{deck_name}}' must be a dictionary"
                assert 'name' in card, f"Card in deck '{{deck_name}}' missing name"
                assert 'count' in card, f"Card in deck '{{deck_name}}' missing count"
                assert 'type' in card, f"Card in deck '{{deck_name}}' missing type"
        
        return True
    except AssertionError as e:
        print(f"❌ Data validation failed: {{e}}")
        return False

def get_stats():
    """Get quick statistics."""
    return {{
        'total_matches': TOTAL_MATCHES,
        'total_wins': TOTAL_WINS,
        'win_rate': WIN_RATE,
        'total_decks': len(DECKS),
        'current_deck': CURRENT_DECK,
        'last_save': LAST_SAVE
    }}

# Auto-validate on import
if __name__ == "__main__":
    if validate_data():
        stats = get_stats()
        print("✅ Data file is valid")
        print(f"📊 Matches: {{stats['total_matches']}} ({{stats['total_wins']}} wins, {{stats['win_rate']:.1f}}% win rate)")
        print(f"🃏 Decks: {{stats['total_decks']}} (current: {{stats['current_deck']}})")
        print(f"📚 History entries: {{len(DECK_HISTORY)}}")
        print(f"💾 Last save: {{stats['last_save']}}")
    else:
        print("❌ Data file validation failed")
'''.format(
                timestamp=datetime.now().isoformat(),
                total_matches=total_matches,
                total_wins=total_wins,
                win_rate=win_rate,
                active_decks=len(decks),
                current_deck=current_deck,
                matches_data=json.dumps(matches, indent=4, default=str),
                decks_data=json.dumps(decks, indent=4),
                history_data=json.dumps(deck_history, indent=4, default=str)
            )
            
            # Write to file
            with open(self.data_file_path, 'w', encoding='utf-8') as f:
                f.write(data_content)
            
            logger.info(f"💾 Saved data: {total_matches} matches, {len(decks)} decks")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save data: {e}")
            return False
    
    def load_data(self) -> Dict[str, Any]:
        """Load data from the user data file."""
        try:
            if not os.path.exists(self.data_file_path):
                logger.warning(f"⚠️ Data file not found: {self.data_file_path}")
                return self.get_default_data()
            
            # Import the data file as a module
            spec = importlib.util.spec_from_file_location("user_data", self.data_file_path)
            user_data = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(user_data)
            
            # Extract data with defaults
            data = {
                'matches': getattr(user_data, 'MATCHES', []),
                'decks': getattr(user_data, 'DECKS', {}),
                'deck_history': getattr(user_data, 'DECK_HISTORY', []),
                'current_deck': getattr(user_data, 'CURRENT_DECK', ''),
                'last_save': getattr(user_data, 'LAST_SAVE', None),
                'data_version': getattr(user_data, 'DATA_VERSION', '1.0.0'),
                'total_matches': getattr(user_data, 'TOTAL_MATCHES', 0),
                'total_wins': getattr(user_data, 'TOTAL_WINS', 0)
            }
            
            logger.info(f"📖 Loaded data: {len(data['matches'])} matches, {len(data['decks'])} decks")
            return data
            
        except Exception as e:
            logger.error(f"❌ Failed to load data: {e}")
            logger.info("🔄 Using default data")
            return self.get_default_data()
    
    def get_default_data(self) -> Dict[str, Any]:
        """Get default data structure."""
        return {
            'matches': [],
            'decks': {
                "Pikachu ex": [
                    {"name": "Pikachu ex", "count": 3, "type": "Pokemon"},
                    {"name": "Raichu", "count": 2, "type": "Pokemon"},
                    {"name": "Professor's Research", "count": 4, "type": "Trainer"},
                    {"name": "Ultra Ball", "count": 4, "type": "Trainer"},
                    {"name": "Electric Energy", "count": 12, "type": "Energy"}
                ],
                "Charizard ex": [
                    {"name": "Charizard ex", "count": 3, "type": "Pokemon"},
                    {"name": "Charmander", "count": 4, "type": "Pokemon"},
                    {"name": "Arcanine ex", "count": 2, "type": "Pokemon"},
                    {"name": "Professor's Research", "count": 4, "type": "Trainer"},
                    {"name": "Fire Energy", "count": 10, "type": "Energy"}
                ]
            },
            'deck_history': [
                {
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'change': 'Initial Setup',
                    'cards': 'Created starter decks',
                    'reason': 'Application initialization'
                }
            ],
            'current_deck': 'Pikachu ex',
            'last_save': None,
            'data_version': '2.1.0',
            'total_matches': 0,
            'total_wins': 0
        }
    
    def save_current_state(self):
        """Save the current state by loading and re-saving data."""
        try:
            data = self.load_data()
            return self.save_data(
                data['matches'],
                data['decks'],
                data['deck_history'],
                data['current_deck']
            )
        except Exception as e:
            logger.error(f"❌ Failed to save current state: {e}")
            return False
    
    def get_save_status(self) -> Dict[str, Any]:
        """Get auto-save status information."""
        try:
            if os.path.exists(self.data_file_path):
                stat_result = os.stat(self.data_file_path)
                last_modified = datetime.fromtimestamp(stat_result.st_mtime)
                
                data = self.load_data()
                
                return {
                    'file_exists': True,
                    'last_modified': last_modified.isoformat(),
                    'last_save': data.get('last_save'),
                    'file_size': stat_result.st_size,
                    'data_version': data.get('data_version', 'Unknown'),
                    'total_matches': data.get('total_matches', 0),
                    'total_decks': len(data.get('decks', {}))
                }
            else:
                return {
                    'file_exists': False,
                    'error': 'Data file not found'
                }
        except Exception as e:
            logger.error(f"❌ Failed to get save status: {e}")
            return {
                'file_exists': False,
                'error': str(e)
            }
    
    def migrate_data(self, from_version: str, to_version: str):
        """Migrate data between versions if needed."""
        logger.info(f"🔄 Migrating data from {from_version} to {to_version}")
        
        # Add migration logic here as needed
        # For now, just ensure all fields exist
        
        data = self.load_data()
        
        # Ensure all matches have required fields
        for match in data['matches']:
            if 'timestamp' not in match and 'date' in match:
                match['timestamp'] = f"{match['date']}T12:00:00"
            if 'winCondition' not in match:
                match['winCondition'] = 'Prize Cards Taken'
            if 'turns' not in match:
                match['turns'] = ''
        
        # Save migrated data
        self.save_data(
            data['matches'],
            data['decks'],
            data['deck_history'],
            data['current_deck']
        )
        
        logger.info("✅ Data migration completed")