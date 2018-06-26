from locust import HttpLocust, TaskSet, task

class MyTaskSet(TaskSet):
    @task
    def search_vim(self):
        self.client.get("/search?query=vim&format=json")
    @task
    def search_python3(self):
        self.client.get("/search?query=python3&format=json")
    @task
    def search_vim_python3(self):
        self.client.get("/search?query=vim,python=3&format=json")

class MyLocust(HttpLocust):
    task_set = MyTaskSet
    min_wait = 100
    max_wait = 1000