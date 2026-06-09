"""Filament management routes"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import Filament, PrintHistory
from app.forms import FilamentForm, UsageForm, LinkNewSpoolForm

filaments_bp = Blueprint('filaments', __name__, url_prefix='/filaments')


@filaments_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_filament():
    """Add a new filament spool"""
    form = FilamentForm()
    
    if form.validate_on_submit():
        filament = Filament(
            user_id=current_user.id,
            type=form.type.data,
            color=form.color.data,
            color_hex=form.color_hex.data,
            starting_weight=form.starting_weight.data,
            current_weight=form.starting_weight.data  # Initially full
        )
        
        db.session.add(filament)
        db.session.commit()
        
        flash(f'Filament "{filament.type} - {filament.color}" added successfully!', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('filaments/add_filament.html', title='Add Filament', form=form)


@filaments_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_filament(id):
    """Edit an existing filament"""
    filament = Filament.query.get_or_404(id)
    
    # Ensure user owns this filament
    if filament.user_id != current_user.id:
        abort(403)
    
    form = FilamentForm()
    
    if form.validate_on_submit():
        # Calculate the difference in starting weight
        weight_diff = form.starting_weight.data - filament.starting_weight
        
        filament.type = form.type.data
        filament.color = form.color.data
        filament.color_hex = form.color_hex.data
        filament.starting_weight = form.starting_weight.data
        # Adjust current weight proportionally
        filament.current_weight += weight_diff
        
        db.session.commit()
        
        flash(f'Filament "{filament.type} - {filament.color}" updated successfully!', 'success')
        return redirect(url_for('main.index'))
    
    # Pre-populate form with current values
    if request.method == 'GET':
        form.type.data = filament.type
        form.color.data = filament.color
        form.color_hex.data = filament.color_hex or '#808080'
        form.starting_weight.data = filament.starting_weight
    
    return render_template('filaments/edit_filament.html', title='Edit Filament', form=form, filament=filament)


@filaments_bp.route('/<int:id>/archive', methods=['POST'])
@login_required
def archive_filament(id):
    """Archive a filament"""
    filament = Filament.query.get_or_404(id)
    
    # Ensure user owns this filament
    if filament.user_id != current_user.id:
        abort(403)
    
    filament.archive()
    db.session.commit()
    
    flash(f'Filament "{filament.type} - {filament.color}" archived.', 'info')
    return redirect(url_for('main.index'))


@filaments_bp.route('/<int:id>/unarchive', methods=['POST'])
@login_required
def unarchive_filament(id):
    """Unarchive a filament"""
    filament = Filament.query.get_or_404(id)
    
    # Ensure user owns this filament
    if filament.user_id != current_user.id:
        abort(403)
    
    filament.unarchive()
    db.session.commit()
    
    flash(f'Filament "{filament.type} - {filament.color}" unarchived.', 'success')
    return redirect(url_for('filaments.archived'))


@filaments_bp.route('/<int:id>/history')
@login_required
def filament_history(id):
    """View print history for a filament"""
    filament = Filament.query.get_or_404(id)
    
    # Ensure user owns this filament
    if filament.user_id != current_user.id:
        abort(403)
    
    # Get all print history records
    history = filament.print_history.all()
    
    return render_template('filaments/filament_history.html', 
                         title=f'History - {filament.type} {filament.color}',
                         filament=filament, 
                         history=history)


@filaments_bp.route('/<int:id>/add-usage', methods=['GET', 'POST'])
@login_required
def add_usage(id):
    """Add usage record to a filament"""
    filament = Filament.query.get_or_404(id)
    
    # Ensure user owns this filament
    if filament.user_id != current_user.id:
        abort(403)
    
    # Don't allow adding usage to archived filaments
    if filament.is_archived:
        flash('Cannot add usage to archived filament.', 'warning')
        return redirect(url_for('filaments.filament_history', id=filament.id))
    
    form = UsageForm()
    overflow = False
    overflow_amount = 0
    
    if form.validate_on_submit():
        weight_used = form.weight_used.data
        
        # Check if usage exceeds remaining weight
        if weight_used > filament.current_weight:
            overflow = True
            overflow_amount = weight_used - filament.current_weight
            flash(f'Usage ({weight_used}g) exceeds remaining weight ({filament.current_weight:.1f}g). '
                  f'Please add a new spool to account for the overflow of {overflow_amount:.1f}g.', 'warning')
            # Store data in session for the overflow modal
            return render_template('filaments/add_usage.html',
                                 title='Add Usage',
                                 form=form,
                                 filament=filament,
                                 overflow=True,
                                 overflow_amount=overflow_amount,
                                 weight_used=weight_used,
                                 print_name=form.print_name.data,
                                 component_name=form.component_name.data)
        
        # Add usage record
        filament.add_usage(
            weight_used=weight_used,
            print_name=form.print_name.data,
            component_name=form.component_name.data
        )
        
        db.session.commit()
        
        status_msg = f'Usage recorded: {weight_used}g used.'
        if filament.is_archived:
            status_msg += ' Filament is now empty and has been archived.'
        
        flash(status_msg, 'success')
        return redirect(url_for('filaments.filament_history', id=filament.id))
    
    return render_template('filaments/add_usage.html',
                         title='Add Usage',
                         form=form,
                         filament=filament,
                         overflow=overflow)


@filaments_bp.route('/<int:id>/add-usage-with-overflow', methods=['POST'])
@login_required
def add_usage_with_overflow(id):
    """Add usage with overflow to a new spool"""
    filament = Filament.query.get_or_404(id)
    
    # Ensure user owns this filament
    if filament.user_id != current_user.id:
        abort(403)
    
    # Get form data
    weight_used = float(request.form.get('weight_used'))
    print_name = request.form.get('print_name')
    component_name = request.form.get('component_name')
    
    # New spool data
    new_type = request.form.get('new_type')
    new_color = request.form.get('new_color')
    new_color_hex = request.form.get('new_color_hex', '#808080')
    new_starting_weight = float(request.form.get('new_starting_weight'))
    
    # Calculate overflow
    overflow_amount = weight_used - filament.current_weight
    
    # Record usage on current spool (use all remaining weight)
    filament.add_usage(
        weight_used=filament.current_weight,
        print_name=print_name,
        component_name=component_name
    )
    
    # Create new spool
    new_filament = Filament(
        user_id=current_user.id,
        type=new_type,
        color=new_color,
        color_hex=new_color_hex,
        starting_weight=new_starting_weight,
        current_weight=new_starting_weight - overflow_amount
    )
    db.session.add(new_filament)
    
    # Record overflow usage on new spool
    new_filament.add_usage(
        weight_used=overflow_amount,
        print_name=print_name,
        component_name=f'{component_name} (overflow from previous spool)'
    )
    
    db.session.commit()
    
    flash(f'Usage recorded across spools. Old spool archived, new spool created with {new_filament.current_weight:.1f}g remaining.', 'success')
    return redirect(url_for('main.index'))


@filaments_bp.route('/archived')
@login_required
def archived():
    """View archived filaments"""
    archived_filaments = Filament.query.filter_by(
        user_id=current_user.id,
        is_archived=True
    ).order_by(Filament.archived_at.desc()).all()
    
    return render_template('filaments/archived.html',
                         title='Archived Filaments',
                         filaments=archived_filaments)
