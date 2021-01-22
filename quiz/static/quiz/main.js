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

document.addEventListener("DOMContentLoaded", function() {
    const count = document.getElementById('count');
    const details = document.getElementById('details');
    const player = document.getElementById('player');

    let time = parseInt(sessionStorage.getItem("time"));
    if (time === null) time = 10;
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
                count.innerHTML = "";
            }
        }

        player.play().then(() => {
            count.innerText = time.toString();
            if (time === 0)
                step();
            else
                setTimeout(step, 1000);
        }).catch(() => {
            count.innerText = "Enable Autoplay (in the address bar) and press Play!";
       });
    }


    player.addEventListener('canplaythrough', play);
    player.addEventListener('ended', () => { location.reload(); });
    player.addEventListener('waiting', () => { waiting = true; })
    player.addEventListener('playing', () => { waiting = false; })
});

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

document.addEventListener("DOMContentLoaded", function () {
    const results = document.getElementById("results-div");

    if (sessionStorage.getItem("results") !== null) {
        results.innerHTML = sessionStorage.getItem("results");
    }
    else {
        results.innerHTML = document.getElementById('results-template').innerHTML;
        console.log(results.outerHTML)
    }
    sessionStorage.setItem("results", results.innerHTML);

    const observer = new MutationObserver(function (mutationsList, observer) {
        sessionStorage.setItem("results", results.innerHTML);
    });
    observer.observe(results, {attributes: true, childList: true, subtree: true, characterData: true});

    for(let playerField of document.getElementsByClassName('form-control user-field player-field')){
        playerField.onchange = function (value){
            playerField.outerHTML = playerField.outerHTML.replace(/value=".*"/, 'value="'+playerField.value+'"');
        };
    }

    let time = sessionStorage.getItem("time");
    if(time === null) time = 10;

    const timeRange = document.getElementById('time-range');
    timeRange.value = time;
    document.getElementById('time-range-out').innerText = timeRange.value;
    timeRange.addEventListener('change', function(){
        document.getElementById('time-range-out').innerText = timeRange.value;
        sessionStorage['time'] = timeRange.value;
    });
});
