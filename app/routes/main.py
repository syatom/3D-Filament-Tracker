"""Main application routes"""
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from sqlalchemy import func, desc
from app import db
from app.models import Filament, PrintHistory

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@login_required
def index():
    """Home dashboard showing active filaments"""
    # Get search/filter parameters
    search_query = request.args.get('q', '').strip()
    
    # Base query for active filaments
    query = Filament.query.filter_by(user_id=current_user.id, is_archived=False)
    
    # Apply search filter
    if search_query:
        search_pattern = f'%{search_query}%'
        query = query.filter(
            db.or_(
                Filament.type.ilike(search_pattern),
                Filament.color.ilike(search_pattern)
            )
        )
    
    # Order by creation date (newest first)
    filaments = query.order_by(Filament.created_at.desc()).all()
    
    return render_template('home.html',
                         title='My Filaments',
                         filaments=filaments,
                         search_query=search_query)


@main_bp.route('/statistics')
@login_required
def statistics():
    """Statistics and reporting page"""
    # Total filament used (sum of all print history)
    total_used_query = db.session.query(
        func.sum(PrintHistory.weight_used)
    ).join(Filament).filter(
        Filament.user_id == current_user.id
    ).scalar()
    
    total_used = total_used_query or 0
    
    # Usage by filament type
    usage_by_type = db.session.query(
        Filament.type,
        func.sum(PrintHistory.weight_used).label('total_used')
    ).join(PrintHistory).filter(
        Filament.user_id == current_user.id
    ).group_by(Filament.type).order_by(desc('total_used')).all()
    
    # Prepare type chart data
    type_labels = [type_name for type_name, _ in usage_by_type]
    type_data = [float(total) for _, total in usage_by_type]
    
    # Usage by color
    usage_by_color = db.session.query(
        Filament.color,
        func.sum(PrintHistory.weight_used).label('total_used')
    ).join(PrintHistory).filter(
        Filament.user_id == current_user.id
    ).group_by(Filament.color).order_by(desc('total_used')).all()
    
    # Prepare color chart data
    color_labels = [color for color, _ in usage_by_color]
    color_data = [float(total) for _, total in usage_by_color]
    
    # Most used filaments (individual spools)
    most_used_filaments = db.session.query(
        Filament,
        func.sum(PrintHistory.weight_used).label('total_used')
    ).join(PrintHistory).filter(
        Filament.user_id == current_user.id
    ).group_by(Filament.id).order_by(desc('total_used')).limit(10).all()
    
    # Total number of prints (count unique multicolor_print_id groups + single prints)
    # Handle backward compatibility - if column doesn't exist yet, just count all records
    try:
        # Count single-color prints (multicolor_print_id is NULL)
        single_color_prints = PrintHistory.query.join(Filament).filter(
            Filament.user_id == current_user.id,
            PrintHistory.multicolor_print_id.is_(None)
        ).count()
        
        # Count distinct multicolor prints (unique multicolor_print_id values)
        multicolor_prints = db.session.query(
            func.count(func.distinct(PrintHistory.multicolor_print_id))
        ).join(Filament).filter(
            Filament.user_id == current_user.id,
            PrintHistory.multicolor_print_id.isnot(None)
        ).scalar() or 0
        
        total_prints = single_color_prints + multicolor_prints
    except Exception:
        # Fallback if multicolor_print_id column doesn't exist yet
        total_prints = PrintHistory.query.join(Filament).filter(
            Filament.user_id == current_user.id
        ).count()
    
    # Active filaments count
    active_count = Filament.query.filter_by(
        user_id=current_user.id,
        is_archived=False
    ).count()
    
    # Archived filaments count
    archived_count = Filament.query.filter_by(
        user_id=current_user.id,
        is_archived=True
    ).count()
    
    # Low filament warnings
    low_filaments = Filament.query.filter_by(
        user_id=current_user.id,
        is_archived=False
    ).all()
    low_filaments = [f for f in low_filaments if f.is_low]
    
    return render_template('statistics.html',
                         title='Statistics',
                         total_used=total_used,
                         usage_by_type=usage_by_type,
                         usage_by_color=usage_by_color,
                         type_labels=type_labels,
                         type_data=type_data,
                         color_labels=color_labels,
                         color_data=color_data,
                         most_used_filaments=most_used_filaments,
                         total_prints=total_prints,
                         active_count=active_count,
                         archived_count=archived_count,
                         low_filaments=low_filaments)
