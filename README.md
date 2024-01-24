## Anime Themes Quiz

**Official instance: [quiz.moe](https://quiz.moe)**

Have you ever had an anime quiz with your friends,
used a YouTube video for that and thought:

> Man, this guy has a shit taste!

Look no further!

Anime Quiz pulls the anime you and your friends watched from
your [MyAnimeList](https://myanimelist.net) profiles and randomly
generates a quiz --- it first chooses one of the participants,
then pulls their MAL list, gets links to themes hosted at
[animethemes.moe](https://animethemes.moe), plays it and gives you
10 seconds (configurable) to guess! Then the whole video is 
uncovered for you to enjoy and the person who guessed can
shout at the gamemaster to add their points to the built-in
scoreboard.

### Features

* MAL lists pulled and cached for 7 days at the server
* animethemes.moe queried and cached for 30 days
* choice of MAL lists
* choice of theme types (OP/ED)
* choice of time to guess
* all hosted online

### Run

If you just want to play, go to [quiz.moe](https://quiz.moe).

If you want to develop or self-host, the recommended way is to
install [Docker](https://docker.com) with Docker Compose and run:
```shell
docker network create server
docker-compose up -d
docker-compose exec anime_quiz python manage.py collectstatic
```

That's it. Anime Quiz will be run at http://localhost:8009.
To rebuild, run `docker-compose build` beforehand.

### Develop

PRs are welcome! The code is licensed under GNU Affero Public Licence 3.
