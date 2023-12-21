import math

from flask import Flask, render_template, request, redirect, url_for, session, flash
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, timedelta
from log import setup_logger

app = Flask(__name__)
app.secret_key = 'joojoosingasong'
app.config['UPLOAD_FOLDER'] = './static'  # Update this path
app.config['JSON_AS_ASCII'] = False

CSV_FILE_PATH = './user_info.csv'
QUESTION_TIME_FILE_PATH = './question_times.csv'
TOTAL_QUESTIONS = 20

# Setup the logger
logger = setup_logger()

if not os.path.exists(CSV_FILE_PATH):
    df = pd.DataFrame(
        columns=['id', 'username', 'team', 'last_completed_question', 'password_hash', 'start_time',
                 'completion_time', 'total_time'])
    df.to_csv(CSV_FILE_PATH, index=False, encoding='utf-8')
if not os.path.exists(QUESTION_TIME_FILE_PATH):
    question_times_df = pd.DataFrame(columns=['user_id', 'username', 'team', 'question_number', 'completion_time'])
    question_times_df.to_csv(QUESTION_TIME_FILE_PATH, index=False, encoding='utf-8')

# Load the CSV file into a DataFrame
def load_users():
    try:
        return pd.read_csv(CSV_FILE_PATH)

    except Exception as e:
        logger.error(f'Error : {e}')
        return render_template('error.html', error_message=e)


# Save the DataFrame to the CSV file
def save_users(df):
    try:
        df.to_csv(CSV_FILE_PATH, index=False)
    except Exception as e:
        logger.error(f'Error : {e}')
        return render_template('error.html', error_message=e)

# Validate a user's login attempt
def validate_login(username, team, password):
    try:
        users_df = load_users()
        user = users_df.loc[(users_df['username'] == username) & (users_df['team'] == team)].squeeze()
        # user = users_df.loc[users_df['username'] == username].squeeze()
        logger.info(f"Attempting login for username: {username}")
        if not user.empty and check_password_hash(user['password_hash'], password):
            logger.info(f'Login successful for username: {username}')
            return user
        else:
            logger.warning(f'Login failed for username: {username}')
    except Exception as e:
        logger.error(f'Error during login for username: {username} : {e}')
        return render_template('error.html', error_message=e)


    return None

# Save a user's progress
def save_progress(user_id, question_number):
    try:
        users_df = load_users()
        current_question_number = users_df.loc[users_df['id'] == user_id, 'last_completed_question']
        if current_question_number.empty or current_question_number.iloc[0] < question_number:
            users_df.loc[users_df['id'] == user_id, 'last_completed_question'] = question_number
            save_users(users_df)
    except Exception as e:
        logger.error(f'Error : {e}')
        return render_template('error.html', error_message=e)


# Function to get the current top 10 users
def get_top_users():
    try:
        users_df = load_users()
        # Convert 'NaT' to None or a specific string
        users_df['completion_time'] = users_df['completion_time'].apply(lambda x: x if pd.notnull(x) else None)
        top_users = users_df.sort_values(by=['last_completed_question', 'total_time'], ascending=[False, True])
        top_users = top_users.head(10)  # Take the top 10
        return top_users[['username', 'team', 'last_completed_question', 'total_time']].to_dict(orient='records')
    except Exception as e:
        logger.error(f'Error : {e}')
        return render_template('error.html', error_message=e)

from datetime import timedelta

def format_duration(seconds):
    if math.isnan(seconds):
        return "N/A"
    else:
        duration = timedelta(seconds=seconds)
        days = duration.days
        hours, remainder = divmod(duration.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{days}d {hours}h {minutes}m {seconds}s"

app.jinja_env.filters['format_duration'] = format_duration

def user_exists(username, team):
    try:
        users_df = load_users()
        return not users_df[(users_df['username'] == username) & (users_df['team'] == team)].empty
    except Exception as e:
        logger.error(f'Error : {e}')
        return render_template('error.html', error_message=e)


def load_correct_answer(question_number):
    try:
        filename = f'answers/{question_number}.txt'
        with open(filename, 'r', encoding='utf-8') as file:
            answers = [answer.replace('\n','') for answer in file.readlines()]
            return answers
    except FileNotFoundError:
        logger.error(f'Answer file not found for question {question_number}')
        return None
    except Exception as e:
        logger.error(f'Error reading answer file for question {question_number}: {e}')
        return None


def load_question_description(question_number):
    try:
        filename = f'questions/{question_number}.txt'
        with open(filename, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        logger.error(f'Question description file not found for question {question_number}')
        return None
    except Exception as e:
        logger.error(f'Error reading question description for question {question_number}: {e}')
        return None


def add_user(username, team, plaintext_password):
    try:
        users_df = load_users()
        # Generate a new user ID
        if users_df.empty:
            new_id = 1  # Starting ID if the DataFrame is empty
        else:
            new_id = users_df['id'].max() + 1

        new_user = pd.DataFrame([{
            'id': new_id,
            'username': username,
            'team': team,
            'password_hash': generate_password_hash(plaintext_password),
            'last_completed_question': 0
        }])

        users_df = pd.concat([users_df, new_user], ignore_index=True)
        save_users(users_df)
    except Exception as e:
        logger.error(f'Error : {e}')



def reset_user_password(username, team, new_password):
    try:
        users_df = load_users()
        # Check if user exists
        user_exists = ((users_df['username'] == username) & (users_df['team'] == team)).any()
        if user_exists:
            # Update the user's password
            users_df.loc[(users_df['username'] == username) & (users_df['team'] == team), 'password_hash'] = generate_password_hash(new_password)
            users_df.loc[(users_df['username'] == username) & (users_df['team'] == team), 'last_completed_question'] = 0
            users_df.loc[(users_df['username'] == username) & (users_df['team'] == team), 'completion_time'] = None
            save_users(users_df)
        else:
            print("User not found")
            add_user(username, team, new_password)
    except Exception as e:
        logger.error(f'Error : {e}')
        return render_template('error.html', error_message=e)

def record_question_completion(user_id, question_number, completion_time):
    question_times_df = pd.read_csv(QUESTION_TIME_FILE_PATH)

    # Check if the user already has a record for this question
    record_exists = question_times_df[(question_times_df['user_id'] == user_id) & (question_times_df['question_number'] == question_number)].empty
    if not record_exists:
        # Update the existing record if the new completion time is better
        existing_record = question_times_df[(question_times_df['user_id'] == user_id) & (question_times_df['question_number'] == question_number)]
        if completion_time < existing_record['completion_time'].iloc[0]:
            question_times_df.loc[(question_times_df['user_id'] == user_id) & (question_times_df['question_number'] == question_number), 'completion_time'] = completion_time
    else:
        # Add a new record
        users_df = load_users()
        user = users_df.loc[users_df['id'] == user_id].squeeze()
        new_record = {'user_id': user_id, 'username': user['username'], 'team': user['team'], 'question_number': question_number, 'completion_time': completion_time}
        question_times_df = pd.concat([question_times_df, pd.DataFrame([new_record])], ignore_index=True)
    # Save the updated DataFrame
    question_times_df.to_csv(QUESTION_TIME_FILE_PATH, index=False)

def get_top_users_for_question(question_number):
    try:
        question_times_df = pd.read_csv(QUESTION_TIME_FILE_PATH)
        top_users = question_times_df[question_times_df['question_number'] == question_number].sort_values(by='completion_time').head(10)
        return top_users[['username', 'team', 'question_number', 'completion_time']].to_dict(orient='records')
    except Exception as e:
        logger.error(f'Error : {e}')
        return



# Use this function to display the top 10 for a specific question

@app.route('/home', methods=['GET', 'POST'])
def home():
    if 'user_id' not in session:
        flash('로그인 해주세요')
        return redirect(url_for('login'))

    users_df = load_users()
    user = users_df.loc[users_df['id'] == session['user_id']].squeeze()

    if user.empty:
        flash('로그인 해주세요')
        return redirect(url_for('login'))

    if request.method == 'POST':
        start_input = request.form.get('game-start-input')
        if start_input == '시작':
            return redirect(url_for('question', question_number=int(user['last_completed_question']) + 1))

    last_completed_question = int(user['last_completed_question'])
    return render_template('home.html', last_completed_question=last_completed_question, top_users=get_top_users())


@app.route('/', methods=['GET', 'POST'])
def login():
    try:
        message = request.args.get('message', '')  # Get the message from the query parameter
        session['login_attempts'] = session.get('login_attempts', 0)

        if request.method == 'POST':
            user_decision = request.form.get('user_decision', 'no')
            username = request.form.get('username')
            team = request.form.get('team')
            password = request.form.get('password')

            if 'user_decision' in request.form:
                if user_decision == 'yes':
                    session['creating_new_account'] = True
                    return render_template('index.html', ask_for_new_password=True, username=username, team=team, top_users=get_top_users())
                # Create a new account and redirect to login
                else:
                    pass
                # add_user(username, team, password)
                # session.clear()
                # return redirect(url_for('index', message='Account created successfully. Please log in.'))
            if session.get('creating_new_account'):
                password = request.form.get('password', '')
                if password:
                    reset_user_password(session['username'], session['team'], password)
                    session.clear()
                    return redirect(url_for('login', message='Password reset successfully. Please log in with your new password.'))
                else:
                    return render_template('index.html', reset_password=True, username=username, team=team,
                                           message="Please enter a new password.", top_users=get_top_users())

            if not username or not team:
                username = request.form.get('username')
                team = request.form.get('team')
                session['username'] = username
                session['team'] = team

            if user_exists(username, team):
                # The user exists, handle login attempt
                if password:
                    user = validate_login(username, team, password)
                    if user is not None:
                        # Login successful
                        session.pop('login_attempts', None)  # Reset login attempts
                        session['user_id'] = int(user['id'])
                        session['last_completed_question'] = int(user['last_completed_question'])
                        # return redirect(url_for('question', question_number=int(user['last_completed_question']) + 1))
                        return redirect(url_for('home'))
                    else:
                        # Login failed
                        session['login_attempts'] += 1
                        if session['login_attempts'] >= 2:
                            return render_template('index.html', ask_new_account=True, username=username, team=team,
                                                   message='비밀번호가 다릅니다. 새로운 계정을 만들까요? 모든 기록은 리셋됩니다', top_users=get_top_users())
                                # return render_template('index.html', ask_if_new=True, username=username, team=team)
                        else:
                            return render_template('index.html', user_exists=True, username=username, team=team, message='비밀번호가 다릅니다. 다시 입력해주세요', top_users=get_top_users())
                else:
                    # Password not provided, request for password
                    session['username'] = username
                    session['team'] = team
                    return render_template('index.html', user_exists=True, username=username, team=team, message='비밀번호를 입력해주세요', top_users=get_top_users())
            else:
                # User does not exist, handle new account creation
                if password:
                    add_user(username, team, password)
                    return redirect(url_for('login', message='아이디 만들기 성공! 로그인 해주세요'))
                else:
                    # Prompt for account creation
                    return render_template('index.html', ask_if_new=True, username=username, team=team, top_users=get_top_users())
            # Render the template with appropriate message for existing users
            return render_template('index.html', user_exists=True, username=username, team=team, message=message, ask_new_account=ask_new_account, top_users=get_top_users())

        # Render the initial template if it's not a POST request or no action was taken
        session.clear()
        return render_template('index.html', message=message, top_users=get_top_users())

    except Exception as e:
        logger.error(f'Error : {e}')
        return render_template('error.html', error_message=e)


@app.route('/question/<int:question_number>', methods=['GET', 'POST'])
def question(question_number):
    try:
        if 'user_id' not in session:
            # If the user is not logged in, redirect to login
            logger.info("Redirecting to login - User not logged in")
            return redirect(url_for('login'))

        # questions = load_questions()
        # question = str(questions.get(question_number))
        question_description = load_question_description(question_number)
        if question_description is None:
            question_description = "Description not available."

        users_df = load_users()
        user = users_df.loc[users_df['id'] == session['user_id']].squeeze()

        from pytz import timezone, utc
        KST = timezone('Asia/Seoul')


        if user.empty:
            # If no user is found, redirect to login
            logger.warning("Redirecting to login - User not found")
            return redirect(url_for('login'))

        if question_number == 1 and pd.isna(user['start_time']):
            now = datetime.now()
            now = utc.localize(now).astimezone(KST)
            users_df.loc[users_df['id'] == session['user_id'], 'start_time'] = now.strftime(
                '%Y-%m-%d %H:%M:%S')
            save_users(users_df)

        if question_number > int(user['last_completed_question']) + 1:
            # Prevent accessing questions ahead of the user's progress
            logger.warning(
                f"Redirecting to question {int(user['last_completed_question']) + 1} - User {user} tried to access ahead")
            return redirect(url_for('question', question_number=int(user['last_completed_question']) + 1))

        if question_number > TOTAL_QUESTIONS:
            if 'completion_time' not in user or pd.isna(user['completion_time']):
                completion_time = datetime.now()
                completion_time = utc.localize(completion_time).astimezone(KST)
                users_df.loc[users_df['id'] == session['user_id'], 'completion_time'] = completion_time.strftime(
                    '%Y-%m-%d %H:%M:%S')
                # Calculate total time consumed
                start_time = pd.to_datetime(user['start_time'])
                end_time = pd.to_datetime(completion_time.strftime(
                    '%Y-%m-%d %H:%M:%S'))
                total_time = end_time - start_time
                users_df.loc[
                    users_df['id'] == session['user_id'], 'total_time'] = total_time.total_seconds()  # in minutes
                save_users(users_df)
                logger.info(f"User {session['user_id']} completed all questions")

            # Record completion time and show completion message
            # user = users_df.loc[users_df['id'] == session['user_id']].squeeze()
            # if 'completion_time' not in user or pd.isna(user['completion_time']):
            #     formatted_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            #     users_df.loc[users_df['id'] == session['user_id'], 'completion_time'] = formatted_time
            #     save_users(users_df)
            #     logger.info(f"User {session['user_id']} completed all questions")
            return render_template('completion.html')  # A template to show completion message

        message = ''
        if request.method == 'POST':
            correct_answers = load_correct_answer(question_number)
            user_answer = str(request.form.get('answer-input'))

            if user_answer in correct_answers:
                logger.info(f"User {session['user_id']} answered right for question {question_number} with '{user_answer}'")
                save_progress(session['user_id'], question_number)
                now = datetime.now()
                now = utc.localize(now).astimezone(KST)
                completion_time = now.strftime('%Y-%m-%d %H:%M:%S')
                record_question_completion(session['user_id'], question_number, completion_time)
                next_question = question_number + 1
                message = '정답을 맞혔습니다!'
                return redirect(url_for('question', question_number=next_question, message=message))
            else:
                logger.info(f"User {session['user_id']} answered wrong for question {question_number} with '{user_answer}'")
                message = '틀렸습니다!'

        return render_template('question.html', question_number=question_number, top_users=get_top_users(), top_users_for_question=get_top_users_for_question(question_number), message=message, question_description=question_description)
    except Exception as e:
        logger.error(f"Error in question route for question number {question_number}: {e}")
        return render_template('error.html', error_message=e)



@app.route('/logout', methods=['POST'])
def logout():
    try:
        session.clear()
        return redirect(url_for('login'))
    except Exception as e:
        logger.error(f'Error : {e}')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_code=404, error_message="The requested page was not found."), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error_code=500, error_message="Internal server error."), 500

# Additional error handlers as needed...


if __name__ == '__main__':
    # Register the filter
    app.run(host='0.0.0.0')