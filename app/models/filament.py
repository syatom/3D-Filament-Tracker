"""Filament model for tracking spools"""
from datetime import datetime
from app import db


class Filament(db.Model):
    """Filament spool model"""
    __tablename__ = 'filaments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    type = db.Column(db.String(100), nullable=False)  # e.g., 'PLA Matte', 'PLA Basic', 'PETG'
    color = db.Column(db.String(50), nullable=False)  # e.g., 'Red', 'Blue', 'Black'
    color_hex = db.Column(db.String(7), nullable=True)  # Hex color code, e.g., '#FF0000'
    starting_weight = db.Column(db.Float, nullable=False)  # in grams
    current_weight = db.Column(db.Float, nullable=False)  # in grams
    is_archived = db.Column(db.Boolean, default=False, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    archived_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    print_history = db.relationship('PrintHistory', backref='filament', lazy='dynamic', 
                                   cascade='all, delete-orphan', order_by='PrintHistory.timestamp.desc()')
    
    @property
    def remaining_weight(self):
        """Calculate remaining weight"""
        return max(0, self.current_weight)
    
    @property
    def remaining_percentage(self):
        """Calculate remaining percentage"""
        if self.starting_weight == 0:
            return 0
        return (self.current_weight / self.starting_weight) * 100
    
    @property
    def is_low(self):
        """Check if filament is running low (<20%)"""
        return self.remaining_percentage < 20
    
    def add_usage(self, weight_used, print_name, component_name):
        """Add usage record and update current weight"""
        from app.models.print_history import PrintHistory
        
        # Create print history record
        history = PrintHistory(
            filament_id=self.id,
            weight_used=weight_used,
            print_name=print_name,
            component_name=component_name
        )
        db.session.add(history)
        
        # Update current weight
        self.current_weight -= weight_used
        
        # Auto-archive if empty
        if self.current_weight <= 0:
            self.current_weight = 0
            self.is_archived = True
            self.archived_at = datetime.utcnow()
        
        return history
    
    def archive(self):
        """Archive this filament"""
        self.is_archived = True
        self.archived_at = datetime.utcnow()
    
    def unarchive(self):
        """Unarchive this filament"""
        self.is_archived = False
        self.archived_at = None
    
    def __repr__(self):
        return f'<Filament {self.type} - {self.color}>'
