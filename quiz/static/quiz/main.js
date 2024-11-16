/*
 *     Copyright (c) 2021-24 Przemysław Buczkowski
 *
 *     This file is part of Anime Quiz.
 *
 *     Anime Quiz is free software: you can redistribute it and/or modify
 *     it under the terms of the GNU Affero General Public License as
 *     published by the Free Software Foundation, either version 3 of
 *     the License, or (at your option) any later version.
 *
 *     Anime Quiz is distributed in the hope that it will be useful,
 *     but WITHOUT ANY WARRANTY; without even the implied warranty of
 *     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *     GNU Affero General Public License for more details.
 *
 *     You should have received a copy of the GNU Affero General Public License
 *     along with Anime Quiz.  If not, see <https://www.gnu.org/licenses/>.
 */

Object.defineProperty(HTMLMediaElement.prototype, 'playing', {
    get: function(){
        return !!(this.currentTime > 0 && !this.paused && !this.ended && this.readyState > 2);
    }
})

function addUser() {
    const template = document.getElementById("username-template");

    document.getElementById("addUserBtn").insertAdjacentHTML(
        "beforebegin", template.innerHTML
    );
}

function removeUser(element) {
    element.parentNode.parentNode.removeChild(element.parentNode);
}

function initRemRamImageHiding() {
    const remram_img = document.getElementById('remram');
    const remram_show = document.getElementById('remram_show');
    const storageKey = "remram_hidden";
    const storageValue = "hidden";

    function hideImage() {
        remram_img.style.display = "none";
        remram_show.style.display = "inline-block";
        sessionStorage.setItem(storageKey, storageValue);
    }
    function showImage() {
        remram_img.style.display = "";
        remram_show.style.display = "none";
        sessionStorage.removeItem(storageKey);
    }

    remram_img.addEventListener("click", hideImage);
    remram_show.addEventListener("click", showImage);

    if (sessionStorage.getItem(storageKey) === storageValue)
        hideImage();
}

async function loadNextSong() {
    const settings_form = document.getElementById('settings-form');
    const next_button = document.getElementById('next-btn');
    const play_button = document.getElementById('play-btn');
    const player_div = document.getElementById("player-div");
    const start_button = document.getElementById("start_button");

    next_button.disabled = true;
    next_button.innerHTML = "Loading next song&mldr;"
    play_button.disabled = true;
    play_button.innerHTML = "Loading&mldr;"
    start_button.disabled = true;
    start_button.innerHTML = "Loading next song&mldr;"

    const url_params = new URLSearchParams(Array.from(new FormData(settings_form)));
    url_params.append("player_only", "yes");
    const url = window.location.href.split('?')[0] + "?" + url_params.toString();
    const response = await fetch(url);

    if (!response.ok) {
        // Just reload the page...
        location.reload();
    }

    // Paste the player div in
    player_div.innerHTML = await response.text();
    play_button.disabled = false;
    play_button.innerText = "Play!"

    // If exists, move the alert where it should be...
    let nav = document.getElementsByTagName("nav")[0];
    let newAlert = player_div.querySelector(".alert");
    let oldAlert = nav.querySelector(".alert");
    if (newAlert !== null) {
        if (oldAlert !== null)
            oldAlert.replaceWith(newAlert);
        else
            nav.appendChild(newAlert);
    }
    // ...or remove the old one
    else if (oldAlert !== null)
        oldAlert.remove();

    initializePlayer();
}

function initializePage() {
    const lyrics_tab = document.getElementById('lyrics-tab');
    const settings_tab = document.getElementById('settings-tab');

    // Set up tab persistence
    if (sessionStorage.getItem("left_tab") === "lyrics")
        lyrics_tab.click();
    lyrics_tab.addEventListener("click", () => {
        sessionStorage.setItem("left_tab", "lyrics");
    });
    settings_tab.addEventListener("click", () => {
        sessionStorage.setItem("left_tab", "settings");
    });

    let time = parseInt(sessionStorage.getItem("time"));
    if (isNaN(time)) time = 10;

    const timeRange = document.getElementById('time-range');
    timeRange.value = time;
    document.getElementById('time-range-out').innerText = timeRange.value;
    timeRange.addEventListener('change', function(){
        document.getElementById('time-range-out').innerText = timeRange.value;
        sessionStorage['time'] = timeRange.value;
    });

    initResultsSaving();
    initRemRamImageHiding();
    initColorMode();
    initializePlayer();
}

function initializePlayer() {
    const count = document.getElementById('count');
    const details = document.getElementById('details');
    const player = document.getElementById('player');
    const player_div = document.getElementById('player-div');
    const lyrics_text = document.getElementById('lyrics-text');
    const lyrics_hidden = document.getElementById('lyrics-hidden');
    const start_button = document.getElementById('start_button');
    const start_button_div = document.getElementById('start_button_div');

    let time = parseInt(sessionStorage.getItem("time"));
    if (isNaN(time)) time = 10;

    let waiting = false; // True when waiting for data.

    function play() {
        player.removeEventListener('canplaythrough', play);

        function step() {
            if (time > 1) {
                if (player.playing)
                    time--;
                count.innerText = time.toString();
                setTimeout(step, 1000);
            }
            else {
                player.style.visibility = 'visible';
                details.style.visibility = 'visible';
                lyrics_text.style.display = '';
                lyrics_hidden.style.display = 'none';
                count.innerHTML = "";
            }
        }

        player.play().then(() => {
            count.innerText = time.toString();
            count.style.display = "";
            player_div.style.display = "flex";
            start_button_div.style.display = "none";
            resizeVideo();
            if (time === 0)
                step();
            else
                setTimeout(step, 1000);
        }).catch((error) => {
            if (error.name === "NotAllowedError") {
                start_button_div.style.display = "block";
                start_button.disabled = false;
                start_button.innerText = "Click to start!"
                count.style.display = "none";
            }
            else {
                start_button.innerText = "Failed to load :("
                console.error(error, error.stack);
            }
        });
    }

    start_button.addEventListener('click', play);
    player.addEventListener('canplaythrough', play);
    player.addEventListener('ended', loadNextSong);
    player.addEventListener('waiting', () => { waiting = true; })
    player.addEventListener('playing', () => { waiting = false; })

    addEventListener('resize', resizeVideo);
}

document.addEventListener("DOMContentLoaded", initializePage);

function resizeVideo() {
    // Just kill me.
    const nav = document.getElementsByTagName("nav")[0];
    const footer = document.getElementsByTagName("footer")[0];
    const player = document.getElementById("player");
    const info = document.getElementById("info");

    player.style.height = (
        window.innerHeight
        - nav.offsetHeight
        - info.offsetHeight
        - footer.offsetHeight
    ).toFixed() + "px";
}

function addPlayer() {
    const li = document.querySelector(
        "template#results-template"
    ).content.children[0].firstElementChild.cloneNode(true);
    document.getElementById("results").appendChild(li);
}

function removePlayer(element){
    element.parentNode.parentNode.parentNode.removeChild(element.parentNode.parentNode)
}

function clearPlayer(){
    sessionStorage.removeItem('results');
    document.getElementById("results-div").innerHTML = document.getElementById('results-template').innerHTML;
}

function addPoint(element){
    let current = element.parentNode.getElementsByClassName("points")[0].innerText;
    current = parseInt(current) + 1;
    element.parentNode.getElementsByClassName("points")[0].innerText = current;
}

function removePoint(element){
    let current = element.parentNode.getElementsByClassName("points")[0].innerText;
    current = Math.max(parseInt(current) - 1, 0);
    element.parentNode.getElementsByClassName("points")[0].innerText = current;
}

function initResultsSaving() {
    const results = document.getElementById("results-div");

    if (sessionStorage.getItem("results") !== null) {
        results.innerHTML = sessionStorage.getItem("results");
    }
    else {
        results.innerHTML = document.getElementById('results-template').innerHTML;
        sessionStorage.setItem("results", results.innerHTML);
    }

    const observer = new MutationObserver(function (mutationsList, observer) {
        sessionStorage.setItem("results", results.innerHTML);
    });
    observer.observe(results, {attributes: true, childList: true, subtree: true, characterData: true});

    // Update field's value for saving
    for (let playerField of document.getElementsByClassName('form-control user-field player-field')){
        playerField.onchange = function (value){
            playerField.outerHTML = playerField.outerHTML.replace(/value=".*"/, 'value="'+playerField.value+'"');
        };
    }
}

function initColorMode() {
    let mode = sessionStorage.getItem("color-mode");
    if (mode === null) {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches)
            mode = "dark";
    }

    if (mode === "dark")
        _setDarkMode();
}

function _setLightMode() {
    const modeSwitchButton = document.getElementById("mode-switch");
    document.documentElement.setAttribute('data-bs-theme', 'light');

    modeSwitchButton.innerText = "Dark mode";
}

function _setDarkMode() {
    const modeSwitchButton = document.getElementById("mode-switch");
    document.documentElement.setAttribute('data-bs-theme', 'dark');

    modeSwitchButton.innerText = "Light mode";
}

function colorModeSwitch() {
    if (document.documentElement.getAttribute('data-bs-theme') === "dark") {
        _setLightMode();
        sessionStorage.setItem("color-mode", "light");
    } else {
        _setDarkMode();
        sessionStorage.setItem("color-mode", "dark");
    }
}
