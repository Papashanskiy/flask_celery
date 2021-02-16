import random
import time
from flask import Flask, render_template, jsonify, url_for
from celery import Celery

app = Flask(__name__)

app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

celery_app = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery_app.conf.update(app.config)


@celery_app.task(bind=True)
def long_task(self):
    total = random.randint(5, 15)
    for interval in range(total):
        self.update_state(state="PROCESS",
                          meta={
                              'current': interval,
                              'total': total
                          })
        time.sleep(1)
    return {
        'current': 100,
        'total': 100,
        'status': 'Task complete!',
        'result': 'Контент ' + str(random.randint(100, 1000))
    }


@app.route('/')
def hello_world():
    return render_template('index.html')


@app.route('/longtask', methods=['POST'])
def longtask():
    task = long_task.apply_async()
    return jsonify({}), 202, {'Location': url_for('taskstatus', task_id=task.id)}


@app.route('/status/<task_id>')
def taskstatus(task_id):
    task = long_task.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'current': 0,
            'total': 1,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info)
        }
    return jsonify(response)


if __name__ == '__main__':
    app.run(debug=True)
