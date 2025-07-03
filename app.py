#!/usr/bin/env python3
"""
Pokemon TCG Tracker - Flask Backend
Main application entry point with auto-save functionality.

Features:
- RESTful API for match and deck data
- Auto-save to separate data file
- Data persistence across app updates
- Import/export functionality
- Real-time statistics
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime
import os
import sys
import logging

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from services.autosave_service import AutoSaveService
from services.match_service import MatchService
from services.deck_service import DeckService
from services.analytics_service import AnalyticsService
from services.export_service import ExportService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(config_class=Config):
    """Application factory pattern for creating Flask app."""
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config.from_object(config_class)
    
    # Enable CORS for frontend communication
    CORS(app, origins=['http://localhost:3000', 'http://127.0.0.1:3000', 'http://localhost:5000'])
    
    # Initialize services
    autosave_service = AutoSaveService(app.config['DATA_FILE'])
    match_service = MatchService(autosave_service)
    deck_service = DeckService(autosave_service)
    analytics_service = AnalyticsService()
    export_service = ExportService()
    
    logger.info("🎮 Pokemon TCG Tracker Backend Starting Up...")
    logger.info(f"📁 Data file: {app.config['DATA_FILE']}")
    logger.info(f"⏰ Auto-save interval: {app.config['AUTO_SAVE_INTERVAL']} seconds")
    
    # ==================================================================================
    # FRONTEND ROUTES
    # ==================================================================================
    
    @app.route('/')
    def index():
        """Serve the main HTML interface."""
        return render_template('index.html')
    
    @app.route('/health')
    def health_check():
        """Health check endpoint."""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '2.1.0'
        })
    
    # ==================================================================================
    # MATCH DATA API ENDPOINTS
    # ==================================================================================
    
    @app.route('/api/matches', methods=['GET'])
    def get_matches():
        """Get all matches."""
        try:
            matches = match_service.get_all_matches()
            logger.info(f"📊 Retrieved {len(matches)} matches")
            return jsonify(matches)
        except Exception as e:
            logger.error(f"❌ Error retrieving matches: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/matches', methods=['POST'])
    def create_match():
        """Create a new match."""
        try:
            match_data = request.get_json()
            if not match_data:
                return jsonify({'error': 'No match data provided'}), 400
            
            match = match_service.create_match(match_data)
            logger.info(f"✅ Created new match: {match_data.get('myDeck', 'Unknown')} vs {match_data.get('opponentDeck', 'Unknown')}")
            return jsonify(match), 201
        except Exception as e:
            logger.error(f"❌ Error creating match: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/matches/<int:match_id>', methods=['PUT'])
    def update_match(match_id):
        """Update an existing match."""
        try:
            match_data = request.get_json()
            if not match_data:
                return jsonify({'error': 'No match data provided'}), 400
            
            match = match_service.update_match(match_id, match_data)
            if match:
                logger.info(f"📝 Updated match {match_id}")
                return jsonify(match)
            else:
                return jsonify({'error': 'Match not found'}), 404
        except Exception as e:
            logger.error(f"❌ Error updating match {match_id}: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/matches/<int:match_id>', methods=['DELETE'])
    def delete_match(match_id):
        """Delete a match."""
        try:
            success = match_service.delete_match(match_id)
            if success:
                logger.info(f"🗑️ Deleted match {match_id}")
                return '', 204
            else:
                return jsonify({'error': 'Match not found'}), 404
        except Exception as e:
            logger.error(f"❌ Error deleting match {match_id}: {e}")
            return jsonify({'error': str(e)}), 500
    
    # ==================================================================================
    # DECK DATA API ENDPOINTS
    # ==================================================================================
    
    @app.route('/api/decks', methods=['GET'])
    def get_decks():
        """Get all decks."""
        try:
            decks = deck_service.get_all_decks()
            logger.info(f"🃏 Retrieved {len(decks)} deck(s)")
            return jsonify(decks)
        except Exception as e:
            logger.error(f"❌ Error retrieving decks: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/decks', methods=['POST'])
    def create_deck():
        """Create a new deck."""
        try:
            deck_data = request.get_json()
            if not deck_data:
                return jsonify({'error': 'No deck data provided'}), 400
            
            deck = deck_service.create_deck(deck_data)
            logger.info(f"✅ Created new deck: {deck_data.get('name', 'Unknown')}")
            return jsonify(deck), 201
        except Exception as e:
            logger.error(f"❌ Error creating deck: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/decks/<deck_name>', methods=['PUT'])
    def update_deck(deck_name):
        """Update an existing deck."""
        try:
            deck_data = request.get_json()
            if not deck_data:
                return jsonify({'error': 'No deck data provided'}), 400
            
            deck = deck_service.update_deck(deck_name, deck_data)
            if deck:
                logger.info(f"📝 Updated deck: {deck_name}")
                return jsonify(deck)
            else:
                return jsonify({'error': 'Deck not found'}), 404
        except Exception as e:
            logger.error(f"❌ Error updating deck {deck_name}: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/decks/<deck_name>', methods=['DELETE'])
    def delete_deck(deck_name):
        """Delete a deck."""
        try:
            success = deck_service.delete_deck(deck_name)
            if success:
                logger.info(f"🗑️ Deleted deck: {deck_name}")
                return '', 204
            else:
                return jsonify({'error': 'Deck not found'}), 404
        except Exception as e:
            logger.error(f"❌ Error deleting deck {deck_name}: {e}")
            return jsonify({'error': str(e)}), 500
    
    # ==================================================================================
    # DECK HISTORY API ENDPOINTS
    # ==================================================================================
    
    @app.route('/api/deck-history', methods=['GET'])
    def get_deck_history():
        """Get deck modification history."""
        try:
            history = deck_service.get_deck_history()
            logger.info(f"📚 Retrieved {len(history)} history entries")
            return jsonify(history)
        except Exception as e:
            logger.error(f"❌ Error retrieving deck history: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/deck-history', methods=['POST'])
    def add_deck_history_entry():
        """Add a deck history entry."""
        try:
            history_data = request.get_json()
            if not history_data:
                return jsonify({'error': 'No history data provided'}), 400
            
            entry = deck_service.add_history_entry(history_data)
            logger.info(f"📝 Added deck history entry: {history_data.get('change', 'Unknown')}")
            return jsonify(entry), 201
        except Exception as e:
            logger.error(f"❌ Error adding deck history entry: {e}")
            return jsonify({'error': str(e)}), 500
    
    # ==================================================================================
    # CURRENT DECK API ENDPOINTS
    # ==================================================================================
    
    @app.route('/api/current-deck', methods=['GET'])
    def get_current_deck():
        """Get the currently selected deck."""
        try:
            current_deck = deck_service.get_current_deck()
            return jsonify({'currentDeck': current_deck})
        except Exception as e:
            logger.error(f"❌ Error retrieving current deck: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/current-deck', methods=['POST'])
    def set_current_deck():
        """Set the currently selected deck."""
        try:
            data = request.get_json()
            if not data or 'currentDeck' not in data:
                return jsonify({'error': 'No current deck provided'}), 400
            
            success = deck_service.set_current_deck(data['currentDeck'])
            if success:
                logger.info(f"🎯 Set current deck to: {data['currentDeck']}")
                return jsonify({'currentDeck': data['currentDeck']})
            else:
                return jsonify({'error': 'Failed to set current deck'}), 500
        except Exception as e:
            logger.error(f"❌ Error setting current deck: {e}")
            return jsonify({'error': str(e)}), 500
    
    # ==================================================================================
    # ANALYTICS API ENDPOINTS
    # ==================================================================================
    
    @app.route('/api/analytics/win-rate')
    def get_win_rate():
        """Calculate overall win rate."""
        try:
            matches = match_service.get_all_matches()
            win_rate = analytics_service.calculate_win_rate(matches)
            return jsonify({'win_rate': win_rate})
        except Exception as e:
            logger.error(f"❌ Error calculating win rate: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/analytics/deck-performance')
    def get_deck_performance():
        """Get performance statistics for all decks."""
        try:
            matches = match_service.get_all_matches()
            performance = analytics_service.calculate_deck_performance(matches)
            return jsonify(performance)
        except Exception as e:
            logger.error(f"❌ Error calculating deck performance: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/analytics/matchup-analysis')
    def get_matchup_analysis():
        """Get detailed matchup analysis."""
        try:
            matches = match_service.get_all_matches()
            analysis = analytics_service.calculate_matchup_analysis(matches)
            return jsonify(analysis)
        except Exception as e:
            logger.error(f"❌ Error calculating matchup analysis: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/analytics/first-player-advantage')
    def get_first_player_advantage():
        """Calculate first player advantage statistics."""
        try:
            matches = match_service.get_all_matches()
            advantage = analytics_service.calculate_first_player_advantage(matches)
            return jsonify(advantage)
        except Exception as e:
            logger.error(f"❌ Error calculating first player advantage: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/analytics/win-condition-breakdown')
    def get_win_condition_breakdown():
        """Get win condition breakdown statistics."""
        try:
            matches = match_service.get_all_matches()
            breakdown = analytics_service.calculate_win_condition_breakdown(matches)
            return jsonify(breakdown)
        except Exception as e:
            logger.error(f"❌ Error calculating win condition breakdown: {e}")
            return jsonify({'error': str(e)}), 500
    
    # ==================================================================================
    # AUTO-SAVE API ENDPOINTS
    # ==================================================================================
    
    @app.route('/api/autosave', methods=['POST'])
    def autosave():
        """Auto-save all data to the data file."""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Update all data through services
            if 'matches' in data:
                match_service.bulk_update_matches(data['matches'])
            
            if 'decks' in data:
                deck_service.bulk_update_decks(data['decks'])
            
            if 'deckHistory' in data:
                deck_service.bulk_update_history(data['deckHistory'])
            
            if 'currentDeck' in data:
                deck_service.set_current_deck(data['currentDeck'])
            
            # Force save
            autosave_service.save_current_state()
            
            logger.info("💾 Auto-save completed successfully")
            return jsonify({
                'status': 'saved',
                'timestamp': datetime.now().isoformat(),
                'matches_count': len(data.get('matches', [])),
                'decks_count': len(data.get('decks', {}))
            })
        except Exception as e:
            logger.error(f"❌ Auto-save failed: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/autosave/status')
    def autosave_status():
        """Get auto-save status and last save time."""
        try:
            status = autosave_service.get_save_status()
            return jsonify(status)
        except Exception as e:
            logger.error(f"❌ Error getting auto-save status: {e}")
            return jsonify({'error': str(e)}), 500
    
    # ==================================================================================
    # IMPORT/EXPORT API ENDPOINTS
    # ==================================================================================
    
    @app.route('/api/export')
    def export_data():
        """Export all data as JSON."""
        try:
            data = export_service.export_all_data(
                matches=match_service.get_all_matches(),
                decks=deck_service.get_all_decks(),
                history=deck_service.get_deck_history(),
                current_deck=deck_service.get_current_deck()
            )
            logger.info(f"📤 Exported data: {len(data['matches'])} matches, {len(data['decks'])} decks")
            return jsonify(data)
        except Exception as e:
            logger.error(f"❌ Error exporting data: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/import', methods=['POST'])
    def import_data():
        """Import data from JSON."""
        try:
            import_data_payload = request.get_json()
            if not import_data_payload:
                return jsonify({'error': 'No import data provided'}), 400
            
            result = export_service.import_all_data(
                import_data_payload,
                match_service,
                deck_service
            )
            
            # Force save after import
            autosave_service.save_current_state()
            
            logger.info(f"📥 Imported data: {result}")
            return jsonify(result)
        except Exception as e:
            logger.error(f"❌ Error importing data: {e}")
            return jsonify({'error': str(e)}), 500
    
    # ==================================================================================
    # ERROR HANDLERS
    # ==================================================================================
    
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(400)
    def bad_request_error(error):
        return jsonify({'error': 'Bad request'}), 400
    
    logger.info("✅ Pokemon TCG Tracker Backend Ready!")
    return app

# ==================================================================================
# APPLICATION ENTRY POINT
# ==================================================================================

if __name__ == '__main__':
    app = create_app()
    
    # Create templates directory if it doesn't exist
    templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
        logger.info(f"📁 Created templates directory: {templates_dir}")
    
    # Print startup information
    print("\n" + "="*60)
    print("🎮 POKEMON TCG TRACKER BACKEND")
    print("="*60)
    print(f"🌐 Server starting on: http://localhost:5000")
    print(f"📊 API available at: http://localhost:5000/api/")
    print(f"💾 Data file: {app.config['DATA_FILE']}")
    print(f"⏰ Auto-save: Every {app.config['AUTO_SAVE_INTERVAL']} seconds")
    print(f"🔧 Debug mode: {app.config['DEBUG']}")
    print("="*60)
    print("📝 Endpoints available:")
    print("   GET  /                    - Main HTML interface")
    print("   GET  /health             - Health check")
    print("   GET  /api/matches        - Get all matches")
    print("   POST /api/matches        - Create new match")
    print("   GET  /api/decks          - Get all decks")
    print("   POST /api/autosave       - Auto-save data")
    print("   GET  /api/export         - Export all data")
    print("   POST /api/import         - Import data")
    print("="*60)
    print("🚀 Ready to track your Pokemon TCG matches!")
    print("="*60 + "\n")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=app.config['DEBUG'],
        threaded=True
    )