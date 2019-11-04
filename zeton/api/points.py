from flask import request, redirect, url_for, abort, g, flash
from werkzeug.security import generate_password_hash, check_password_hash

import zeton.data_access.bans
import zeton.data_access.points
import datetime
from zeton import auth
from zeton.api import bp
import datetime
from zeton.data_access import users


def max_permission(child_id, exercise_id, days, max_column):
    now = datetime.datetime.now() - datetime.timedelta(days= days)
    dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
    history = zeton.data_access.points.get_points_history_limits(child_id, dt_string, exercise_id)
    act_count = history.__len__()

    if act_count > 0:
        limit = history[0][max_column]
        if act_count >= limit:
            return False
    return True


@bp.route("/child/<child_id>/points/add/<points>/<ex_id>/<details>", methods=['POST'])
@bp.route("/child/<child_id>/points/add/<points>/<ex_id>", methods=['POST'])
@auth.login_required
@auth.logged_child_or_caregiver_only
def add_points(child_id, points, ex_id, details=0):
    if max_permission(child_id, ex_id, 1, 'max_day') and max_permission(child_id, ex_id, 7, 'max_week'):
        logged_user_id = g.user_data['id']
        return_url = request.args.get('return_url', '/')

        if ex_id == '0':
            points = request.form['points']
        try:
            added_points = int(points)
        except ValueError as ex:
            print(ex)
            return {'message': 'Bad request'}, 400

        if added_points > 0:
            zeton.data_access.points.change_points_by(child_id, added_points, logged_user_id)
            zeton.data_access.points.add_exp(added_points, child_id, ex_id)

        if(details!=0):
            return_url=f'views.task_detail'
        else:
            return_url='views.child'

        role = g.user_data['role']
        if role == 'child':
            return redirect(return_url)
        else:
            return redirect(url_for(return_url, child_id=child_id))
    else:
        flash(f'W ciągu ostatniej doby został przekroczony limit punktów')
        return redirect(url_for('views.child', child_id=child_id))


@bp.route("/child/<child_id>/points/use", methods=['POST'])
@auth.login_required
@auth.logged_child_or_caregiver_only
def use_points(child_id):
    logged_user_id = g.user_data['id']
    child_id = int(child_id)

    return_url = request.args.get('return_url', '/')

    current_points = zeton.data_access.points.get_only_points(child_id)
    try:
        used_points = int(request.form['points'])
    except ValueError as ex:
        print(ex)
        return {'message': 'Bad request'}, 400

    if used_points > 0:
        if used_points <= current_points:
            zeton.data_access.points.change_points_by(child_id, -used_points, logged_user_id)
        else:
            missing_points = abs(current_points - used_points)
            if missing_points == 1:
                points_word = 'punktu'
            else:
                points_word = 'punktów'
            flash(f'Do tej nagrody brakuje Ci:  {missing_points} {points_word}')

    return redirect(return_url)
