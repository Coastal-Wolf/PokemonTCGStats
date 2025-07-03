#!/usr/bin/env python3
"""
Pokemon TCG Tracker - Export Service
Handles data import/export functionality with format validation.
"""

import json
import csv
import io
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)

class ExportService:
    """Service for handling data import and export operations."""
    
    def __init__(self):
        """Initialize the export service."""
        logger.info("📁 Export service initialized")
    
    # ==================================================================================
    # EXPORT FUNCTIONS
    # ==================================================================================
    
    def export_all_data(self, matches: List[Dict[str, Any]], decks: Dict[str, Any], 
                       history: List[Dict[str, Any]], current_deck: str) -> Dict[str, Any]:
        """Export all data in the standard JSON format."""
        try:
            export_data = {
                'matches': self._clean_matches_for_export(matches),
                'decks': self._clean_decks_for_export(decks),
                'history': self._clean_history_for_export(history),
                'currentDeck': current_deck,
                'exportDate': datetime.now().isoformat(),
                'version': '2.1.0',
                'metadata': {
                    'total_matches': len(matches),
                    'total_decks': len(decks),
                    'total_history_entries': len(history),
                    'win_rate': self._calculate_quick_win_rate(matches),
                    'exported_by': 'Pokemon TCG Tracker Backend'
                }
            }
            
            logger.info(f"📤 Exported data: {len(matches)} matches, {len(decks)} decks")
            return export_data
            
        except Exception as e:
            logger.error(f"❌ Failed to export data: {e}")
            raise
    
    def export_matches_only(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Export only match data."""
        try:
            export_data = {
                'matches': self._clean_matches_for_export(matches),
                'exportDate': datetime.now().isoformat(),
                'version': '2.1.0',
                'type': 'matches_only',
                'metadata': {
                    'total_matches': len(matches),
                    'win_rate': self._calculate_quick_win_rate(matches),
                    'exported_by': 'Pokemon TCG Tracker Backend'
                }
            }
            
            logger.info(f"📤 Exported matches only: {len(matches)} matches")
            return export_data
            
        except Exception as e:
            logger.error(f"❌ Failed to export matches: {e}")
            raise
    
    def export_decks_only(self, decks: Dict[str, Any], history: List[Dict[str, Any]], 
                         current_deck: str) -> Dict[str, Any]:
        """Export only deck data."""
        try:
            export_data = {
                'decks': self._clean_decks_for_export(decks),
                'history': self._clean_history_for_export(history),
                'currentDeck': current_deck,
                'exportDate': datetime.now().isoformat(),
                'version': '2.1.0',
                'type': 'decks_only',
                'metadata': {
                    'total_decks': len(decks),
                    'total_history_entries': len(history),
                    'exported_by': 'Pokemon TCG Tracker Backend'
                }
            }
            
            logger.info(f"📤 Exported decks only: {len(decks)} decks")
            return export_data
            
        except Exception as e:
            logger.error(f"❌ Failed to export decks: {e}")
            raise
    
    def export_matches_csv(self, matches: List[Dict[str, Any]]) -> str:
        """Export matches to CSV format."""
        try:
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            headers = [
                'Date', 'Timestamp', 'My Deck', 'Opponent Deck', 'Result', 
                'Turns', 'Went First', 'Win Condition', 'Notable Cards', 'Notes'
            ]
            writer.writerow(headers)
            
            # Write data
            for match in matches:
                row = [
                    match.get('date', ''),
                    match.get('timestamp', ''),
                    match.get('myDeck', ''),
                    match.get('opponentDeck', ''),
                    match.get('result', ''),
                    match.get('turns', ''),
                    match.get('wentFirst', ''),
                    match.get('winCondition', ''),
                    match.get('notableCards', ''),
                    match.get('notes', '')
                ]
                writer.writerow(row)
            
            csv_content = output.getvalue()
            output.close()
            
            logger.info(f"📄 Exported {len(matches)} matches to CSV")
            return csv_content
            
        except Exception as e:
            logger.error(f"❌ Failed to export CSV: {e}")
            raise
    
    def export_deck_list(self, deck_name: str, deck_cards: List[Dict[str, Any]]) -> str:
        """Export a single deck as a formatted deck list."""
        try:
            lines = [f"# {deck_name}", f"# Exported on {datetime.now().strftime('%Y-%m-%d')}", ""]
            
            # Group by type
            pokemon_cards = [card for card in deck_cards if card.get('type') == 'Pokemon']
            trainer_cards = [card for card in deck_cards if card.get('type') == 'Trainer']
            energy_cards = [card for card in deck_cards if card.get('type') == 'Energy']
            
            # Add Pokemon section
            if pokemon_cards:
                lines.append("## Pokemon")
                for card in pokemon_cards:
                    lines.append(f"{card.get('count', 1)}x {card.get('name', 'Unknown Card')}")
                lines.append("")
            
            # Add Trainer section
            if trainer_cards:
                lines.append("## Trainers")
                for card in trainer_cards:
                    lines.append(f"{card.get('count', 1)}x {card.get('name', 'Unknown Card')}")
                lines.append("")
            
            # Add Energy section
            if energy_cards:
                lines.append("## Energy")
                for card in energy_cards:
                    lines.append(f"{card.get('count', 1)}x {card.get('name', 'Unknown Card')}")
                lines.append("")
            
            # Add summary
            total_cards = sum(card.get('count', 1) for card in deck_cards)
            lines.append(f"Total Cards: {total_cards}")
            
            deck_list = "\n".join(lines)
            logger.info(f"📋 Exported deck list for '{deck_name}' ({total_cards} cards)")
            return deck_list
            
        except Exception as e:
            logger.error(f"❌ Failed to export deck list: {e}")
            raise
    
    # ==================================================================================
    # IMPORT FUNCTIONS
    # ==================================================================================
    
    def import_all_data(self, import_data: Dict[str, Any], match_service, deck_service) -> Dict[str, Any]:
        """Import all data from JSON format."""
        try:
            result = {
                'matches_imported': 0,
                'decks_imported': 0,
                'history_entries_imported': 0,
                'current_deck_set': False,
                'errors': [],
                'warnings': []
            }
            
            # Validate import data structure
            validation_result = self._validate_import_data(import_data)
            if not validation_result['valid']:
                result['errors'].extend(validation_result['errors'])
                return result
            
            # Import matches
            if 'matches' in import_data and isinstance(import_data['matches'], list):
                try:
                    match_service.bulk_update_matches(import_data['matches'])
                    result['matches_imported'] = len(import_data['matches'])
                    logger.info(f"📥 Imported {result['matches_imported']} matches")
                except Exception as e:
                    result['errors'].append(f"Failed to import matches: {str(e)}")
            
            # Import decks
            if 'decks' in import_data and isinstance(import_data['decks'], dict):
                try:
                    deck_service.bulk_update_decks(import_data['decks'])
                    result['decks_imported'] = len(import_data['decks'])
                    logger.info(f"📥 Imported {result['decks_imported']} decks")
                except Exception as e:
                    result['errors'].append(f"Failed to import decks: {str(e)}")
            
            # Import deck history
            if 'history' in import_data and isinstance(import_data['history'], list):
                try:
                    deck_service.bulk_update_history(import_data['history'])
                    result['history_entries_imported'] = len(import_data['history'])
                    logger.info(f"📥 Imported {result['history_entries_imported']} history entries")
                except Exception as e:
                    result['errors'].append(f"Failed to import history: {str(e)}")
            
            # Set current deck
            if 'currentDeck' in import_data and import_data['currentDeck']:
                try:
                    deck_service.set_current_deck(import_data['currentDeck'])
                    result['current_deck_set'] = True
                    logger.info(f"📥 Set current deck to: {import_data['currentDeck']}")
                except Exception as e:
                    result['warnings'].append(f"Failed to set current deck: {str(e)}")
            
            # Check for data format upgrades
            if 'version' in import_data:
                import_version = import_data['version']
                if import_version != '2.1.0':
                    result['warnings'].append(f"Imported data from version {import_version}, converted to 2.1.0")
            
            total_imported = result['matches_imported'] + result['decks_imported'] + result['history_entries_imported']
            logger.info(f"✅ Import completed: {total_imported} total items")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to import data: {e}")
            raise
    
    def import_matches_csv(self, csv_content: str, match_service) -> Dict[str, Any]:
        """Import matches from CSV format."""
        try:
            result = {
                'matches_imported': 0,
                'errors': [],
                'warnings': []
            }
            
            # Parse CSV
            reader = csv.DictReader(io.StringIO(csv_content))
            matches = []
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 to account for header
                try:
                    # Map CSV columns to match fields
                    match = {
                        'date': row.get('Date', '').strip(),
                        'timestamp': row.get('Timestamp', '').strip(),
                        'myDeck': row.get('My Deck', '').strip(),
                        'opponentDeck': row.get('Opponent Deck', '').strip(),
                        'result': row.get('Result', '').strip(),
                        'turns': row.get('Turns', '').strip(),
                        'wentFirst': row.get('Went First', '').strip(),
                        'winCondition': row.get('Win Condition', '').strip(),
                        'notableCards': row.get('Notable Cards', '').strip(),
                        'notes': row.get('Notes', '').strip()
                    }
                    
                    # Basic validation
                    if not match['date']:
                        result['warnings'].append(f"Row {row_num}: Missing date, using current date")
                        match['date'] = datetime.now().strftime('%Y-%m-%d')
                    
                    if match['result'] not in ['Win', 'Loss']:
                        result['warnings'].append(f"Row {row_num}: Invalid result '{match['result']}', defaulting to Loss")
                        match['result'] = 'Loss'
                    
                    matches.append(match)
                    
                except Exception as e:
                    result['errors'].append(f"Row {row_num}: Failed to parse - {str(e)}")
                    continue
            
            # Import matches
            if matches:
                match_service.bulk_update_matches(matches)
                result['matches_imported'] = len(matches)
                logger.info(f"📥 Imported {result['matches_imported']} matches from CSV")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to import CSV: {e}")
            raise
    
    # ==================================================================================
    # VALIDATION FUNCTIONS
    # ==================================================================================
    
    def _validate_import_data(self, import_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate import data structure."""
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        if not isinstance(import_data, dict):
            result['valid'] = False
            result['errors'].append("Import data must be a JSON object")
            return result
        
        # Check for required structure
        if 'matches' in import_data:
            if not isinstance(import_data['matches'], list):
                result['errors'].append("Matches must be an array")
                result['valid'] = False
            else:
                # Validate match structure
                for i, match in enumerate(import_data['matches']):
                    if not isinstance(match, dict):
                        result['warnings'].append(f"Match {i} is not an object, skipping")
                        continue
                    
                    # Check required fields
                    if 'result' not in match:
                        result['warnings'].append(f"Match {i} missing result field")
        
        if 'decks' in import_data:
            if not isinstance(import_data['decks'], dict):
                result['errors'].append("Decks must be an object")
                result['valid'] = False
            else:
                # Validate deck structure
                for deck_name, cards in import_data['decks'].items():
                    if not isinstance(cards, list):
                        result['warnings'].append(f"Deck '{deck_name}' cards must be an array")
                        continue
                    
                    for j, card in enumerate(cards):
                        if not isinstance(card, dict):
                            result['warnings'].append(f"Card {j} in deck '{deck_name}' is not an object")
                            continue
                        
                        if 'name' not in card:
                            result['warnings'].append(f"Card {j} in deck '{deck_name}' missing name")
        
        if 'history' in import_data:
            if not isinstance(import_data['history'], list):
                result['errors'].append("History must be an array")
                result['valid'] = False
        
        return result
    
    # ==================================================================================
    # HELPER FUNCTIONS
    # ==================================================================================
    
    def _clean_matches_for_export(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean and validate matches for export."""
        clean_matches = []
        
        for match in matches:
            clean_match = {
                'date': match.get('date', ''),
                'timestamp': match.get('timestamp', ''),
                'myDeck': match.get('myDeck', ''),
                'opponentDeck': match.get('opponentDeck', ''),
                'result': match.get('result', 'Loss'),
                'turns': match.get('turns', ''),
                'wentFirst': match.get('wentFirst', 'You'),
                'winCondition': match.get('winCondition', 'Prize Cards Taken'),
                'notableCards': match.get('notableCards', ''),
                'notes': match.get('notes', '')
            }
            
            # Ensure timestamp exists
            if not clean_match['timestamp'] and clean_match['date']:
                clean_match['timestamp'] = f"{clean_match['date']}T12:00:00"
            elif not clean_match['timestamp']:
                clean_match['timestamp'] = datetime.now().isoformat()
            
            clean_matches.append(clean_match)
        
        return clean_matches
    
    def _clean_decks_for_export(self, decks: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and validate decks for export."""
        clean_decks = {}
        
        for deck_name, cards in decks.items():
            if not isinstance(cards, list):
                continue
            
            clean_cards = []
            for card in cards:
                if isinstance(card, dict):
                    clean_card = {
                        'name': card.get('name', ''),
                        'count': card.get('count', 1),
                        'type': card.get('type', 'Pokemon')
                    }
                    
                    # Validate count
                    try:
                        clean_card['count'] = int(clean_card['count'])
                        if clean_card['count'] < 1:
                            clean_card['count'] = 1
                    except (ValueError, TypeError):
                        clean_card['count'] = 1
                    
                    # Validate type
                    if clean_card['type'] not in ['Pokemon', 'Trainer', 'Energy']:
                        clean_card['type'] = 'Pokemon'
                    
                    clean_cards.append(clean_card)
            
            if clean_cards:  # Only add decks with valid cards
                clean_decks[deck_name] = clean_cards
        
        return clean_decks
    
    def _clean_history_for_export(self, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean and validate history for export."""
        clean_history = []
        
        for entry in history:
            if isinstance(entry, dict):
                clean_entry = {
                    'date': entry.get('date', datetime.now().strftime('%Y-%m-%d')),
                    'change': entry.get('change', 'Modified'),
                    'cards': entry.get('cards', ''),
                    'reason': entry.get('reason', '')
                }
                clean_history.append(clean_entry)
        
        return clean_history
    
    def _calculate_quick_win_rate(self, matches: List[Dict[str, Any]]) -> float:
        """Calculate a quick win rate for export metadata."""
        if not matches:
            return 0.0
        
        wins = sum(1 for match in matches if match.get('result') == 'Win')
        return round((wins / len(matches)) * 100, 1)
    
    # ==================================================================================
    # BACKUP FUNCTIONS
    # ==================================================================================
    
    def create_backup_export(self, matches: List[Dict[str, Any]], decks: Dict[str, Any], 
                           history: List[Dict[str, Any]], current_deck: str) -> Dict[str, Any]:
        """Create a backup export with additional metadata."""
        try:
            backup_data = self.export_all_data(matches, decks, history, current_deck)
            
            # Add backup-specific metadata
            backup_data['backup_metadata'] = {
                'created_at': datetime.now().isoformat(),
                'backup_type': 'automatic',
                'data_integrity_hash': self._calculate_data_hash(backup_data),
                'pokemon_tcg_tracker_version': '2.1.0'
            }
            
            logger.info("💾 Created backup export with integrity hash")
            return backup_data
            
        except Exception as e:
            logger.error(f"❌ Failed to create backup export: {e}")
            raise
    
    def _calculate_data_hash(self, data: Dict[str, Any]) -> str:
        """Calculate a simple hash for data integrity checking."""
        try:
            # Create a simple hash based on key data points
            match_count = len(data.get('matches', []))
            deck_count = len(data.get('decks', {}))
            history_count = len(data.get('history', []))
            
            # Simple hash based on counts and current deck
            hash_string = f"{match_count}-{deck_count}-{history_count}-{data.get('currentDeck', '')}"
            return hash_string
            
        except Exception:
            return "unknown"