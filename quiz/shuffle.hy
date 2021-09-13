(import
	    [django.core.cache [cache]]
		[animethemes_dl [OPTIONS :as ANIMETHEMES_OPTIONS]]
		[animethemes_dl.parsers.myanimelist [get-raw-mal filter-mal]]
)

; Refetch user MAL data every week.
(setv MAL_EXPIRE 60 * 60 * 24 * 7)
; Refetch animethemes data every month.
(setv THEMES_EXPIRE 60 * 60 * 24 * 30)

(defn get-user-themes [user statuses]
	  "
	  Gets playable themes along with their last occurence.
	  Arguments:
	   - user: str - a name of a MAL user.
	   - statuses: List[int] - a list of statuses from which to pull MAL data.
	  "

	  (defn get-mal-data []
	        "Pulls the data from MyAnimeList, checking in the cache first."
			(setv mal-cache-key (+ "mal-cache-" user))
			(lif (setx mal-cache (cache.get mal-cache-key))
			     mal-cache
				 (do (setv mal-data (get-raw-mal user))
					 (cache.set mal-cache-key mal-data MAL_EXPIRE)
					 mal-data)))

	  (setv mal-data (get-mal-data))
	  
	  ; Filter by statuses.
	  ; Unfortunately these are passed to the animethemes
	  ; library with a global.
	  ; filter-mal returns tuples of id and titles.
	  (assoc ANIMETHEMES_OPTIONS "statuses" statuses)
	  (setv mal-data (filter-mal mal_data))

	  (defn get-theme [[anime-id anime-name]]
	        "
			Gets animethemes.moe data for an anime from the cache.
			If its not in the cache, it enqueues its fetching 
			and returns :enqueued.
			"
			(setv theme-cache-key (+ "theme-cache-" anime-id))
			(lif (setx theme-cache (cache.get theme-cache-key))
			     theme-cache
				 (do (fetch-theme.delay anime-id anime-name))
					 :enqueued))
	   
	  
	  (setv fetched-themes (map get-theme mal-data))

	  mal_data)
	     
