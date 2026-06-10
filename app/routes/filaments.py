"""Filament management routes"""
import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Filament, PrintHistory
from app.forms import FilamentForm, UsageForm, LinkNewSpoolForm, MulticolorUsageForm

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
    
    # Group multicolor prints and gather related filaments info
    multicolor_groups = {}
    for record in history:
        if record.is_multicolor and record.multicolor_print_id not in multicolor_groups:
            # Get all related filaments for this multicolor print
            related_records = PrintHistory.query.filter_by(
                multicolor_print_id=record.multicolor_print_id
            ).all()
            
            related_filaments = []
            for rel_record in related_records:
                rel_filament = Filament.query.get(rel_record.filament_id)
                if rel_filament:
                    related_filaments.append({
                        'filament': rel_filament,
                        'weight_used': rel_record.weight_used,
                        'record_id': rel_record.id
                    })
            
            multicolor_groups[record.multicolor_print_id] = related_filaments
    
    return render_template('filaments/filament_history.html', 
                         title=f'History - {filament.type} {filament.color}',
                         filament=filament, 
                         history=history,
                         multicolor_groups=multicolor_groups)


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


@filaments_bp.route('/multicolor-usage', methods=['GET', 'POST'])
@login_required
def add_multicolor_usage():
    """Add usage record for a multicolor (AMS) print across multiple filaments"""
    form = MulticolorUsageForm()
    
    # Get all active filaments for selection
    active_filaments = Filament.query.filter_by(
        user_id=current_user.id,
        is_archived=False
    ).order_by(Filament.type, Filament.color).all()
    
    if not active_filaments:
        flash('No active filaments available. Please add a filament first.', 'warning')
        return redirect(url_for('main.index'))
    
    if form.validate_on_submit():
        # Get selected filaments and their usage weights from request.form
        selected_filament_ids = request.form.getlist('filament_ids[]')
        
        if not selected_filament_ids or len(selected_filament_ids) == 0:
            flash('Please select at least one filament.', 'warning')
            return render_template('filaments/add_multicolor_usage.html',
                                 title='Add Multicolor Print',
                                 form=form,
                                 active_filaments=active_filaments)
        
        if len(selected_filament_ids) > 16:
            flash('Maximum 16 filaments allowed for AMS multicolor prints.', 'warning')
            return render_template('filaments/add_multicolor_usage.html',
                                 title='Add Multicolor Print',
                                 form=form,
                                 active_filaments=active_filaments)
        
        # Collect usage data and validate
        usage_data = []
        overflow_detected = False
        overflow_filament = None
        overflow_amount = 0
        
        for filament_id in selected_filament_ids:
            filament = Filament.query.get(int(filament_id))
            if not filament or filament.user_id != current_user.id or filament.is_archived:
                flash('Invalid filament selection.', 'danger')
                return redirect(url_for('filaments.add_multicolor_usage'))
            
            weight_key = f'weight_{filament_id}'
            try:
                weight_used = float(request.form.get(weight_key, 0))
            except (ValueError, TypeError):
                flash(f'Invalid weight for {filament.type} - {filament.color}.', 'danger')
                return render_template('filaments/add_multicolor_usage.html',
                                     title='Add Multicolor Print',
                                     form=form,
                                     active_filaments=active_filaments)
            
            if weight_used <= 0:
                flash(f'Weight must be greater than 0 for {filament.type} - {filament.color}.', 'danger')
                return render_template('filaments/add_multicolor_usage.html',
                                     title='Add Multicolor Print',
                                     form=form,
                                     active_filaments=active_filaments)
            
            # Check for overflow
            if weight_used > filament.current_weight:
                overflow_detected = True
                overflow_filament = filament
                overflow_amount = weight_used - filament.current_weight
                break
            
            usage_data.append({
                'filament': filament,
                'weight_used': weight_used
            })
        
        # Handle overflow
        if overflow_detected:
            flash(f'Usage for {overflow_filament.type} - {overflow_filament.color} ({overflow_filament.current_weight:.1f}g available) '
                  f'exceeds remaining weight. Please adjust or handle overflow.', 'warning')
            # Store form data for resubmission
            return render_template('filaments/add_multicolor_usage.html',
                                 title='Add Multicolor Print',
                                 form=form,
                                 active_filaments=active_filaments,
                                 overflow=True,
                                 overflow_filament=overflow_filament,
                                 overflow_amount=overflow_amount,
                                 selected_ids=selected_filament_ids,
                                 form_data=request.form)
        
        # Generate unique ID for this multicolor print
        multicolor_print_id = str(uuid.uuid4())
        
        # Create print history records for all selected filaments
        for data in usage_data:
            filament = data['filament']
            weight_used = data['weight_used']
            
            # Create print history record with multicolor_print_id
            history = PrintHistory(
                filament_id=filament.id,
                weight_used=weight_used,
                print_name=form.print_name.data,
                component_name=form.component_name.data,
                multicolor_print_id=multicolor_print_id
            )
            db.session.add(history)
            
            # Update filament weight
            filament.current_weight -= weight_used
            
            # Auto-archive if empty
            if filament.current_weight <= 0:
                filament.current_weight = 0
                filament.is_archived = True
                from datetime import datetime
                filament.archived_at = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'Multicolor print "{form.print_name.data}" recorded successfully across {len(usage_data)} filaments!', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('filaments/add_multicolor_usage.html',
                         title='Add Multicolor Print',
                         form=form,
                         active_filaments=active_filaments)


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


@filaments_bp.route('/<int:filament_id>/usage/<int:usage_id>/delete', methods=['POST'])
@login_required
def delete_usage(filament_id, usage_id):
    """Delete a usage record and restore weight to filament. For multicolor prints, deletes all related entries."""
    # Get the filament and verify ownership
    filament = Filament.query.get_or_404(filament_id)
    
    if filament.user_id != current_user.id:
        abort(403)
    
    # Get the usage record
    usage = PrintHistory.query.get_or_404(usage_id)
    
    # Verify the usage belongs to this filament
    if usage.filament_id != filament.id:
        return jsonify({'success': False, 'error': 'Usage does not belong to this filament'}), 400
    
    # Check if this is a multicolor print
    is_multicolor = usage.is_multicolor
    multicolor_print_id = usage.multicolor_print_id
    
    if is_multicolor:
        # Delete all related multicolor print entries
        related_usages = PrintHistory.query.filter_by(multicolor_print_id=multicolor_print_id).all()
        
        total_weight_restored = 0
        filaments_updated = []
        
        for related_usage in related_usages:
            related_filament = Filament.query.get(related_usage.filament_id)
            
            # Verify ownership of all related filaments
            if related_filament.user_id != current_user.id:
                return jsonify({'success': False, 'error': 'Unauthorized access to related filament'}), 403
            
            # Restore weight
            related_filament.current_weight += related_usage.weight_used
            total_weight_restored += related_usage.weight_used
            
            # Unarchive if needed
            if related_filament.is_archived and related_filament.current_weight > 0:
                related_filament.unarchive()
            
            filaments_updated.append(f'{related_filament.type} - {related_filament.color}')
            
            # Delete the usage record
            db.session.delete(related_usage)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Multicolor print deleted. {len(related_usages)} entries removed from {len(filaments_updated)} filaments.',
            'weight_restored': total_weight_restored,
            'filaments_updated': filaments_updated,
            'is_multicolor': True
        })
    else:
        # Single-color print deletion (original logic)
        weight_to_restore = usage.weight_used
        
        # Restore weight to filament
        filament.current_weight += weight_to_restore
        
        # Check if filament should be unarchived
        was_unarchived = False
        if filament.is_archived and filament.current_weight > 0:
            filament.unarchive()
            was_unarchived = True
        
        # Delete the usage record
        db.session.delete(usage)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Usage deleted. {weight_to_restore:.1f}g restored to filament.',
            'weight_restored': weight_to_restore,
            'new_current_weight': filament.current_weight,
            'was_unarchived': was_unarchived,
            'is_multicolor': False
        })
