"""
Initial User Profile Generator
==============================

Generate initial user profiles based on actual movielens users

    - http://files.grouplens.org/datasets/movielens/ml-20m-README.html

User profile logic:
    Persona:
        Education distribution: 40% secondary; 30% Bachelor; 20% Master; 10% Phd;
        Gender distribution: 50% male; 50% female
        Income: 43% low; 41% medium; 16% high based on below
            Low: less than $25k; Medium: $25-75k; High: greater than $75k https://en.wikipedia.org/wiki/Personal_income_in_the_United_States
        Income and education utilize the same probability to ensure that a higher education will likely have a better income.
    Preferences:
        Sample from the real users using MovieLens 20M Dataset


Author: Shuo Zhang
"""
import os
import csv
import random
from code.user.simulated_user import SimulatedUser

MOVIELEN_PATH = "code/user/"

EDUCATION = ["Secondary", "Bachelor", "Master", "PhD"]
EDUCATION_DIST = [0.4, 0.3, 0.2, 0.1]
GENDER = ["Male", "Female"]
GENDER_DIST = [0.5, 0.5]
INCOME = ["Low", "Medium", "High"]
INCOME_DIST = [0.43, 0.41, 0.16]
LOCATION = {}


class UserGenerator:
    """Class for generate random users."""

    def __init__(self):
        self.__mov = self.movies()

    @staticmethod
    def movies():
        mov = dict()
        with open(os.path.join(MOVIELEN_PATH, "movies.csv")) as f:
            csv_data = csv.reader(f)
            for i, line in enumerate(csv_data):
                if i == 0:
                    continue
                m_id, m, gs = line
                mov[m_id] = {
                    "title": m,
                    "genres": gs
                }
        return mov

    def samp(self, pro, dist, attribute):
        """Based on random generated probability, determine the persona category"""
        acc_pro = 0
        for i, item in enumerate(dist):
            acc_pro += item
            if pro < acc_pro:
                return attribute[i]

    def generate_persona(self):
        """Based on random generated probability, determine persona"""
        age = random.randint(22, 50)
        pro = random.uniform(0, 1)
        gender = self.samp(pro=random.uniform(0, 1), dist=GENDER_DIST, attribute=GENDER)
        education = self.samp(pro=pro, dist=EDUCATION_DIST, attribute=EDUCATION)
        income = self.samp(pro=pro, dist=INCOME_DIST, attribute=INCOME)
        return age, gender, education, income

    @staticmethod
    def rate_pre(rate):
        """Preference exceeding 2.5 is taken as positive"""
        if float(rate) >= 4:
            return 1
        elif float(rate) <= 2:
            return -1
        else:
            return 0


    def rates(self, if_title=True):
        """
        Dump the ratings to get genres preferences over files.
        genre_preference = sum preference_of_movie_has_this_genre / num_of_movie_has_this genre

        :param if_title: to disp movie id or movie title
        :return:
        """
        user_all = {}
        self.__mov = self.movies()
        with open(os.path.join(MOVIELEN_PATH, "ratings.csv")) as f:
            csv_data = csv.reader(f)
            for i, line in enumerate(csv_data):
                if i == 0:
                    continue
                if i == 100000:
                    break
                userId, movieId, rating, timestamp = line
                genres = self.__mov.get(movieId).get("genres")
                title = self.__mov.get(movieId).get("title")
                if userId not in user_all:
                    user_all[userId] = {
                        "movies": {},
                        "genres": {}
                    }
                if if_title:
                    user_all[userId]["movies"][title] = self.rate_pre(rate=rating)
                else:
                    user_all[userId]["movies"][movieId] = self.rate_pre(rate=rating)
                for genre in genres.split("|"):
                    if genre not in user_all[userId]["genres"]:
                        user_all[userId]["genres"][genre] = []
                    user_all[userId]["genres"][genre].append(rating)
        return user_all

    @staticmethod
    def rate_pre1(rate):
        """Preference exceeding 2.5 is taken as positive"""
        if float(rate) >= 3.5:
            return 1
        elif float(rate) <= 2:
            return -1
        else:
            return 0
        # return 1 if float(rate) > 2.5 else -1

    def initial(self, num_user=5, num_movie=8, num_genre=8, if_title=True):
        """
        Create example initial user profiles.

        :param num_user: number of examples users
        :param num_movie: number of movies with references
        :param num_genre: number of geners with references
        :param if_title: to disp movie id or movie title
        :return:
        """
        user_all = self.rates(if_title=if_title)
        users = list()
        for i in range(num_user):
            age, gender, education, income = self.generate_persona()
            userID = str(random.randint(1, 700))
            movie = {v: user_all.get(userID).get("movies")[v] for v in
                     [list(user_all.get(userID).get("movies").keys())[k] for k in range(num_movie)]}
            genres = user_all.get(userID).get("genres")
            genres_norm = {k: self.rate_pre1(sum([float(k) for k in v]) / len(v)) for k, v in genres.items()}
            genres_samp = {v: genres_norm[v] for v in [list(genres_norm.keys())[k] for k in range(num_genre)]}
            persona = {
                "age": age,
                "genda": gender,
                "education": education,
                "income": income
            }
            user = SimulatedUser(persona=persona, preferences=[movie, genres_samp])
            user.print_user()
            users.append(user)
        return users


if __name__ == "__main__":
    per = UserGenerator()
    print(per.initial(num_user=10, num_movie=5, num_genre=5, if_title=True))
