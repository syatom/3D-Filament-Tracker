"""Print history model for tracking usage"""
from datetime import datetime
from app import db


class PrintHistory(db.Model):
    """Print history record model"""
    __tablename__ = 'print_history'
    
    id = db.Column(db.Integer, primary_key=True)
    filament_id = db.Column(db.Integer, db.ForeignKey('filaments.id'), nullable=False, index=True)
    weight_used = db.Column(db.Float, nullable=False)  # in grams
    print_name = db.Column(db.String(200), nullable=False)
    component_name = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    multicolor_print_id = db.Column(db.String(36), nullable=True, index=True)  # UUID for grouped multicolor prints
    
    @property
    def is_multicolor(self):
        """Check if this is part of a multicolor print"""
        return self.multicolor_print_id is not None
    
    def __repr__(self):
        return f'<PrintHistory {self.print_name} - {self.weight_used}g>'
