import pandas as pd
from matplotlib import pyplot as plt
import matplotlib.font_manager as fm
import re
from datetime import datetime
import seaborn as sns


user_data = pd.read_csv('user_info.csv')
path_to_font = 'ganwon.ttf'
font_promp = fm.FontProperties(fname=path_to_font)

def attempts_per_person(file_path):
    pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d{3} - INFO - \[app.py:\d+\] - User (\d+) answered (right|wrong) for question (\d+)'
    data = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            match = re.search(pattern, line)
            if match:
                timestamp, user_id, _, question = match.groups()
                start_time = datetime(2023, 12, 22, 15, 0)
                end_time = datetime(2023, 12, 22, 18, 0)
                if datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S') >= start_time and datetime.strptime(timestamp,
                                                                                                         '%Y-%m-%d %H:%M:%S') < end_time:
                    data.append({
                        'user_id': int(user_id),
                        'question': int(question)
                    })
    df = pd.DataFrame(data)

    # count the number of attempts for each question
    attempts_per_question = df['question'].value_counts()

    average_attempts_per_question = attempts_per_question.mean()

    # Count the number of attempts by each user and get the top user
    attempts_per_user = df['user_id'].value_counts()
    top_10_users = attempts_per_user.head(10)
    top_10_usernames = user_data.set_index('id')['username'].to_dict()
    top_10_users_with_names = top_10_users.rename(index=top_10_usernames)

    plt.figure(figsize=(8, 8))
    top_10_users_with_names.plot.pie(autopct='%1.1f%%', startangle=140)
    plt.title('Top 10 Users by Number of Attempts')
    plt.ylabel('')  # This hides the y-label

    # Save the figure to a file
    plt.savefig('pie_chart.png')

def solve_time_analysis():
    # Calculate the number of participants
    num_participants = user_data['username'].nunique()

    # Calculate the average total time in seconds
    # First, we need to filter out NaN values in the 'total_time' column
    valid_times = user_data['total_time'].dropna()

    # Calculate the average time in seconds
    average_time_seconds = valid_times.mean()

    # Convert seconds to hours and minutes
    average_time_hours = int(average_time_seconds // 3600)
    average_time_minutes = int((average_time_seconds % 3600) // 60)

    print(num_participants, average_time_hours, average_time_minutes)

def people_per_questions():
    completed_questions = user_data['last_completed_question'].value_counts().sort_index()

    plt.figure(figsize=(10,6))
    completed_questions.plot(kind='bar',color='blue')
    plt.title('각 문제 당 푼 사람들 수', fontproperties=font_promp, fontsize=20)
    plt.xlabel('문제 번호', fontproperties=font_promp, fontsize=20)
    plt.ylabel('푼 사람들 수', fontproperties=font_promp, fontsize=20)
    plt.xticks(rotation=0)
    plt.yticks(list(range(0,completed_questions.values.max()+1)), rotation=0)
    plt.savefig('analy2')


# Function to read and process the log file
def time_took_per_question(file_path):
    pattern1 = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d{3} - INFO - \[app.py:\d+\] - User (\d+) answered right for question (\d+)'

    data = []

    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            match = re.search(pattern1, line)
            if match:
                timestamp, user_id, question = match.groups()
                start_time = datetime(2023, 12, 22, 15, 0)
                end_time = datetime(2023, 12, 22, 18, 0)
                if datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S') >= start_time and datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S') < end_time:
                    data.append({
                        'timestamp': datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S'),
                        'user_id': int(user_id),
                        'question': int(question)
                    })


    df_ori = pd.DataFrame(data)
    df = pd.DataFrame(data)
    # Calculating the time taken for each answer
    df.sort_values(by=['user_id', 'timestamp'], inplace=True)
    df['time_taken'] = df.groupby('user_id')['timestamp'].diff().dt.total_seconds()
    # drop first question
    df = df[df.question!=1]
    # Calculate the average time taken for each question
    average_time_per_question = df.groupby('question')['time_taken'].mean() /60

    print(average_time_per_question)

    plt.figure(figsize=(10, 6))
    average_time_per_question.plot(kind='bar', color='blue')
    plt.title('각 문제 당 걸린 평균 시간', fontproperties=font_promp, fontsize=20)
    plt.xlabel('문제 번호', fontproperties=font_promp, fontsize=20)
    plt.ylabel('걸린 시간 (분)', fontproperties=font_promp, fontsize=20)
    plt.xticks(rotation=0)
    # plt.yticks(list(range(0, average_time_per_question.values.max() + 1)), rotation=0)
    plt.savefig('analy3.png')

if __name__=='__main__':
    # time_took_per_question('20231222.log')
    attempts_per_person('20231222.log')
    # solve_time_analysis()