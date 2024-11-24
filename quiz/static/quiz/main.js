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
/* global localStorage, MutationObserver, addEventListener, HTMLMediaElement, location */

Object.defineProperty(HTMLMediaElement.prototype, 'playing', {
  get: function () {
    return !!(this.currentTime > 0 && !this.paused && !this.ended && this.readyState > 2)
  }
})

function addUser (username) {
  const template = document.getElementById('username-template')

  const newUser = template.content.querySelector('div.input-group').cloneNode(true)
  if (username !== undefined) {
    const input = newUser.querySelector('input')
    input.value = username
  }

  document.getElementById('addUserBtn').insertAdjacentElement(
    'beforebegin', newUser
  )
}

function removeUser (element) {
  element.parentNode.parentNode.removeChild(element.parentNode)
}

function initRemRamImageHiding () {
  const remramImg = document.getElementById('remram')
  const remramShow = document.getElementById('remram_show')
  const storageKey = 'remram_hidden'
  const storageValue = 'hidden'

  function hideImage () {
    remramImg.style.display = 'none'
    remramShow.style.display = 'inline-block'
    localStorage.setItem(storageKey, storageValue)
  }
  function showImage () {
    remramImg.style.display = ''
    remramShow.style.display = 'none'
    localStorage.removeItem(storageKey)
  }

  remramImg.addEventListener('click', hideImage)
  remramShow.addEventListener('click', showImage)

  if (localStorage.getItem(storageKey) === storageValue) { hideImage() }
}

async function loadNextSong () {
  const settingsForm = document.getElementById('settings-form')
  if (settingsForm.reportValidity() === false) { return }
  saveSettings()

  const nextButton = document.getElementById('next-btn')
  const playButton = document.getElementById('play-btn')
  const playerDiv = document.getElementById('player-div')
  const startButton = document.getElementById('start_button')

  nextButton.disabled = true
  nextButton.innerHTML = 'Loading&mldr;'
  playButton.disabled = true
  playButton.innerHTML = 'Loading&mldr;'
  startButton.disabled = true
  startButton.innerHTML = 'Loading&mldr;'

  const urlParams = new URLSearchParams(Array.from(new FormData(settingsForm)))
  urlParams.append('player_only', 'yes')
  const url = window.location.href.split('?')[0] + '?' + urlParams.toString()
  const response = await fetch(url).catch((error) => {
    // Submit the form to reload the page in case of a network error
    console.error(error)
    settingsForm.submit()
  })

  if (!response.ok) {
    // Just submit the form to reload the page and see the full error
    settingsForm.submit()
  }

  // Paste the player div in
  playerDiv.innerHTML = await response.text()
  playButton.disabled = false
  playButton.innerText = 'Play!'

  // If exists, move the alert where it should be...
  const nav = document.getElementsByTagName('nav')[0]
  const newAlert = playerDiv.querySelector('.alert')
  const oldAlert = nav.querySelector('.alert')
  if (newAlert !== null) {
    if (oldAlert !== null) {
      oldAlert.replaceWith(newAlert)
    } else {
      nav.appendChild(newAlert)
    }
  } else if (oldAlert !== null) {
    // ...or remove the old one
    oldAlert.remove()
  }

  // Move the lyrics as well.
  const leftAside = document.getElementById('left-aside')
  const newLyrics = playerDiv.querySelector('#lyrics')
  const oldLyrics = leftAside.querySelector('#lyrics')
  const lyricsTab = leftAside.querySelector('#lyrics-tab')
  oldLyrics.replaceWith(newLyrics)
  if (lyricsTab.ariaSelected === "true") {
    // Reload lyrics tab
    const settingsTab = leftAside.querySelector('#settings-tab')

    settingsTab.click()
    lyricsTab.click()
  }

  initializePlayer()
}

function initSettings () {
  // Load settings
  // Return false if default settings are to be used
  if (localStorage.getItem('settings_saved') !== 'true') {
    addUser('przemub')
    return false
  }

  const checkboxes = document.querySelectorAll('form#settings-form input[type=checkbox]')
  for (const checkbox of checkboxes) {
    const savedValue = localStorage.getItem(checkbox.id)
    if (savedValue === 'true') { checkbox.checked = true } else if (savedValue === 'false') { checkbox.checked = false }
  }

  const savedUsers = localStorage.getItem('users')
  if (savedUsers === null) { addUser('przemub') } else {
    for (const user of savedUsers.split(',')) { addUser(user) }
  }

  return true
}

function saveSettings () {
  const checkboxes = document.querySelectorAll(
    'form#settings-form input[type=checkbox]'
  )
  for (const checkbox of checkboxes) { localStorage.setItem(checkbox.id, checkbox.checked.toString()) }

  const userInputs = document.querySelectorAll(
    'form#settings-form input[name=user]'
  )
  const users = [...userInputs].map((input) => { return input.value }).join(',')
  localStorage.setItem('users', users)

  localStorage.setItem('settings_saved', 'true')
}

function initializePage () {
  const lyricsTab = document.getElementById('lyrics-tab')
  const settingsTab = document.getElementById('settings-tab')

  // Set up tab persistence
  if (localStorage.getItem('left_tab') === 'lyrics') { lyricsTab.click() }
  lyricsTab.addEventListener('click', () => {
    localStorage.setItem('left_tab', 'lyrics')
  })
  settingsTab.addEventListener('click', () => {
    localStorage.setItem('left_tab', 'settings')
  })

  let time = parseInt(localStorage.getItem('time'))
  if (isNaN(time)) time = 10

  const timeRange = document.getElementById('time-range')
  timeRange.value = time
  document.getElementById('time-range-out').innerText = timeRange.value
  timeRange.addEventListener('change', function () {
    document.getElementById('time-range-out').innerText = timeRange.value
    localStorage.time = timeRange.value
  })

  initResultsSaving()
  initRemRamImageHiding()
  initColorMode()
  if (initSettings() === true) {
    // If non-default settings are used, we need to
    // request a new player from the server.
    loadNextSong().then()
  } else { initializePlayer() }
}

function initializePlayer () {
  const count = document.getElementById('count')
  const details = document.getElementById('details')
  const player = document.getElementById('player')
  const playerDiv = document.getElementById('player-div')
  const lyricsText = document.getElementById('lyrics-text')
  const lyricsHidden = document.getElementById('lyrics-hidden')
  const startButton = document.getElementById('start_button')
  const startButtonDiv = document.getElementById('start_button_div')

  let time = parseInt(localStorage.getItem('time'))
  if (isNaN(time)) time = 10

  function play () {
    player.removeEventListener('canplaythrough', play)

    function step () {
      if (time > 1) {
        if (player.playing) { time-- }
        count.innerText = time.toString()
        setTimeout(step, 1000)
      } else {
        player.style.visibility = 'visible'

        localStorage.setItem('settings_saved', 'true')
        details.style.visibility = 'visible'
        lyricsText.style.display = ''
        lyricsHidden.style.display = 'none'
        count.innerHTML = ''
      }
    }

    player.play().then(() => {
      count.innerText = time.toString()
      count.style.display = ''
      playerDiv.style.display = 'flex'
      startButtonDiv.style.display = 'none'
      resizeVideo()
      if (time === 0) { step() } else { setTimeout(step, 1000) }
    }).catch((error) => {
      if (error.name === 'NotAllowedError') {
        startButtonDiv.style.display = 'block'
        startButton.disabled = false
        startButton.innerText = 'Click to start!'
        count.style.display = 'none'
      } else {
        startButton.innerText = 'Failed to load :('
        console.error(error, error.stack)
      }
    })
  }

  startButton.addEventListener('click', play)
  player.addEventListener('canplaythrough', play)
  player.addEventListener('ended', loadNextSong)

  addEventListener('resize', resizeVideo)
}

document.addEventListener('DOMContentLoaded', initializePage)

function resizeVideo () {
  // Just kill me.
  const nav = document.getElementsByTagName('nav')[0]
  const footer = document.getElementsByTagName('footer')[0]
  const player = document.getElementById('player')
  const info = document.getElementById('info')

  player.style.height = (
    window.innerHeight -
        nav.offsetHeight -
        info.offsetHeight -
        footer.offsetHeight
  ).toFixed() + 'px'
}

function addPlayer () {
  const li = document.querySelector(
    'template#results-template'
  ).content.children[0].firstElementChild.cloneNode(true)
  document.getElementById('results').appendChild(li)
}

function removePlayer (element) {
  element.parentNode.parentNode.parentNode.removeChild(element.parentNode.parentNode)
}

function clearPlayer () {
  localStorage.removeItem('results')
  document.getElementById('results-div').innerHTML = document.getElementById('results-template').innerHTML
}

function addPoint (element) {
  let current = element.parentNode.getElementsByClassName('points')[0].innerText
  current = parseInt(current) + 1
  element.parentNode.getElementsByClassName('points')[0].innerText = current
}

function removePoint (element) {
  let current = element.parentNode.getElementsByClassName('points')[0].innerText
  current = Math.max(parseInt(current) - 1, 0)
  element.parentNode.getElementsByClassName('points')[0].innerText = current
}

function initResultsSaving () {
  const results = document.getElementById('results-div')

  if (localStorage.getItem('results') !== null) {
    results.innerHTML = localStorage.getItem('results')
  } else {
    results.innerHTML = document.getElementById('results-template').innerHTML
    localStorage.setItem('results', results.innerHTML)
  }

  const observer = new MutationObserver(function (mutationsList, observer) {
    localStorage.setItem('results', results.innerHTML)
  })
  observer.observe(results, { attributes: true, childList: true, subtree: true, characterData: true })

  // Update field's value for saving
  for (const playerField of document.getElementsByClassName('form-control user-field player-field')) {
    playerField.onchange = function (value) {
      playerField.outerHTML = playerField.outerHTML.replace(/value=".*"/, 'value="' + playerField.value + '"')
    }
  }
}

function initColorMode () {
  let mode = localStorage.getItem('color-mode')
  if (mode === null) {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) { mode = 'dark' }
  }

  if (mode === 'dark') { _setDarkMode() }
}

function _setLightMode () {
  const modeSwitchButton = document.getElementById('mode-switch')
  document.documentElement.setAttribute('data-bs-theme', 'light')

  modeSwitchButton.innerText = 'Dark mode'
}

function _setDarkMode () {
  const modeSwitchButton = document.getElementById('mode-switch')
  document.documentElement.setAttribute('data-bs-theme', 'dark')

  modeSwitchButton.innerText = 'Light mode'
}

function colorModeSwitch () {
  if (document.documentElement.getAttribute('data-bs-theme') === 'dark') {
    _setLightMode()
    localStorage.setItem('color-mode', 'light')
  } else {
    _setDarkMode()
    localStorage.setItem('color-mode', 'dark')
  }
}
