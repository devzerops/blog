"""
Admin category management routes.
Contains routes for creating, editing, and deleting blog categories.
"""

from flask import render_template, redirect, url_for, flash, request
from werkzeug.exceptions import NotFound

from app.database import db
from app.models import Category
from app.forms import CategoryForm
from app.auth import admin_required
from app.routes.admin import bp_admin


@bp_admin.route('/categories', methods=['GET'])
@admin_required
def admin_categories(current_user):
    """List all categories"""
    categories = Category.query.order_by(Category.name).all()
    return render_template('admin/admin_categories_list.html', 
                          categories=categories, 
                          title='카테고리 관리', 
                          current_user=current_user)


@bp_admin.route('/categories/new', methods=['GET', 'POST'])
@admin_required
def admin_add_category(current_user):
    """Add a new category"""
    form = CategoryForm()
    if form.validate_on_submit():
        try:
            category_name = form.name.data
            
            # Check if a category with this name already exists
            existing_category = Category.query.filter_by(name=category_name).first()
            
            if existing_category:
                flash('이미 존재하는 카테고리 이름입니다.', 'danger')
                return render_template('admin/admin_category_form.html', 
                                    form=form, 
                                    title='새 카테고리', 
                                    legend='새 카테고리 생성', 
                                    current_user=current_user)
            
            # Create the category
            category = Category(name=category_name)
            db.session.add(category)
            db.session.commit()
            flash('카테고리가 성공적으로 생성되었습니다.', 'success')
            return redirect(url_for('admin.admin_categories'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating category: {str(e)}")
            flash(f'카테고리 생성 중 오류가 발생했습니다: {str(e)}', 'danger')
    else:
        # 폼 검증 실패 시 오류 메시지 출력
        print(f"Form validation failed. Errors: {form.errors}")
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'danger')
    
    return render_template('admin/admin_category_form.html', form=form, title='New Category', legend='새 카테고리 생성', current_user=current_user)


@bp_admin.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_category(current_user, category_id):
    """Edit an existing category"""
    category = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=category)
    
    if form.validate_on_submit():
        new_name = form.name.data
        
        # Check if name changed and if the new name already exists
        if category.name != new_name:
            existing_category = Category.query.filter(
                (Category.id != category_id) & 
                (Category.name == new_name)
            ).first()
            if existing_category:
                flash('이미 존재하는 카테고리 이름입니다.', 'danger')
                return render_template('admin/admin_category_form.html', form=form, title='카테고리 수정', 
                                    legend=f'카테고리 수정: {category.name}', category=category, current_user=current_user)
        
        # Update category
        category.name = new_name
        db.session.commit()
        flash('카테고리가 성공적으로 업데이트되었습니다.', 'success')
        return redirect(url_for('admin.admin_categories'))
        
    return render_template('admin/admin_category_form.html', form=form, title='Edit Category', legend=f'Edit {category.name}', category=category, current_user=current_user)


@bp_admin.route('/categories/delete/<int:category_id>', methods=['POST'])
@admin_required
def admin_delete_category(current_user, category_id):
    """Delete a category"""
    category = Category.query.get_or_404(category_id)
    if category.posts.count() > 0:
        flash('카테고리를 삭제할 수 없습니다. 하나 이상의 게시물과 연결되어 있습니다. 삭제하기 전에 게시물을 재할당해주세요.', 'danger')
        return redirect(url_for('admin.admin_categories'))
    
    db.session.delete(category)
    db.session.commit()
    flash('카테고리가 성공적으로 삭제되었습니다.', 'success')
    return redirect(url_for('admin.admin_categories'))
