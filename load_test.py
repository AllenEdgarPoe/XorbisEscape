from locust import HttpUser, task, between, TaskSet
import random

class UserBehavior(TaskSet):
    wait_time = between(60,100)

    @task
    def login(self):
        # Random username and team for each request, you can modify this as needed
        username = f"user{random.randint(1, 1000)}"
        team = f"미래전략본부"
        password = "123"  # Use a fixed or generated password

        # Sending POST request to the login endpoint
        self.client.post("/", {
            "username": username,
            "team": team,
            "password": password
        })


class LocustUser(HttpUser):
    host = "<http://35.230.71.42:5000/>"
    tasks = [UserBehavior]
    wait_time = between(1, 4)