(import [anime_quiz.celery [app]]
		[animethemes_dl [AnimeThemesTimeout]]
        [animethemes_dl.parsers [animethemes]])

; Refetch animethemes data every month.
(setv THEMES_EXPIRE 60 * 60 * 24 * 30)

(with-decorator app.quiz
	 (defn fetch-theme [anime-id anime-name]
	 	   "
		   Fetches data about an anime from animethemes.moe
		   and saves it to the cache.
		   "

		   ; Check first if it is not in the cache.
		   ; It may happen when an anime is enqueued for fetching
		   ; twice.
		   (setv theme-cache-key (+ "theme-cache-" anime-id))
		   (when (cache.get theme-cache-key) (return))

		   (setv result (animethems.request-anime [[anime-id anime-name]]))
		   (cond [(instance? AnimeThemesTimeout result) 
		          (do 
				     ; If timed out, sleep and re-run.
		             (print "I have got a timeout. Sleeping for 10 secs.")
		   			 (time.sleep 10)
					 (fetch-theme [anime-id anime-name]))]
				 [(none? result) (cache.set theme-cache-key :missing THEMES_EXPIRE)]
				 [True (cache.set theme-cache-key result THEMES_EXPIRE)]
		   )))

