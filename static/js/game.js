const store = new Vuex.Store({
	state: {
		hfen: '3/4/5/4/3 R MRY',
		colorPlayers: {R:null, Y:null, G:null, C:null, B:null, M:null},
		isTerminal: false,
	},
	mutations: {
		setHfen: function(state, hfen) { state.hfen = hfen },
		setColorPlayers: function(state, colorPlayers) { state.colorPlayers = colorPlayers },
		terminate: function(state) { state.isTerminal = true },
	},
	getters: {
		variant: function(state) {
			return state.hfen.split(' ')[2]
		},
		currentColor: function(state) {
			return state.hfen.split(' ')[1]
		},
		mapRadius: function(state) {
			return (state.hfen.match(/\//g) || []).length / 2
		},
	},
})


var colorMixin = {
	data: function() {
		var colors = {}
		var hue = 0
		for(c of "RYGCBM") {
			colors[c] = {
				normal: 'hsl('+hue+', 100%, 45%)',
				light: 'hsl('+hue+', 70%, 80%)',
			}
			hue += 60
		}

		return {colors: colors}
	},
}


Vue.component('board', {
	delimiters: ['[[', ']]'],
	props: ['x', 'y', 'size', 'hfen'],
	computed: {
		calchfen: function() {
			return this.hfen ?? store.state.hfen
		},
		spaceSize: function() {
			return this.size / store.getters.mapRadius / 2.7
		},
		spaces: function() {
			var radius = store.getters.mapRadius
			var spaces = []

			var chars = this.calchfen.split(' ')[0].replace(/(\d)/g, function(match) {
				return '-'.repeat(match)
			}).split('/').join('')
			var i = 0

			for(q = -radius; q <= radius; q++) {
				var r1 = Math.max(-radius, -q - radius)
				var r2 = Math.min(radius, -q + radius)

				for(r = r1; r <= r2; r++) {
					spaces.push({
						char: ("RYGCBMrygcbm".includes(chars[i]) ? chars[i] : ''),
						q: q,
						r: r,
						x: (this.x + this.spaceSize * (q*Math.sqrt(3)/2 + r*Math.sqrt(3))),
						y: (this.y + this.spaceSize * q * 3/2),
					})

					i++
				}
			}

			return spaces
		},
	},
	template: `<g>
		<logo :x="x" :y="y" :size="size"/>

		<space v-for="space in spaces" :key="space.id" :x="space.x" :y="space.y" :q="space.q" :r="space.r" :char="space.char" :size="spaceSize"/>
	</g>`
})

Vue.component('space', {
	mixins: [colorMixin],
	delimiters: ['[[', ']]'],
	props: ['x', 'y', 'size', 'q', 'r', 'char'],
	computed: {
		pieceSize: function() { return this.size * 0.4 },
		pieceOffset: function() { return this.size * 0.3 },
		canPlay: function() {
			if(typeof IS_LIVE !== 'undefined' && IS_LIVE === false) return false
			if(store.state.isTerminal) return false
			if(!this.$parent.$parent.isMyTurn) return false

			if(this.char == '') return true
			if(this.char == store.getters.currentColor.toLowerCase()) return true

			if(store.getters.currentColor == 'R') {
				if('BG'.includes(this.char)) return true
			} else if(store.getters.currentColor == 'Y') {
				if('MC'.includes(this.char)) return true
			} else if(store.getters.currentColor == 'G') {
				if('RB'.includes(this.char)) return true
			} else if(store.getters.currentColor == 'C') {
				if('YM'.includes(this.char)) return true
			} else if(store.getters.currentColor == 'B') {
				if('GR'.includes(this.char)) return true
			} else if(store.getters.currentColor == 'M') {
				if('CY'.includes(this.char)) return true
			}

			return false
		},
		highlight: function() {
			if(this.canPlay) return this.colors[store.getters.currentColor].light
			else return '#eee'
		},
		style: function() {
			if('RGBcmy'.includes(this.char)) return 'mix-blend-mode:screen'
			else if('rgbCMY'.includes(this.char)) return 'mix-blend-mode:multiply'
			else return ''
		},
	},
	methods: {
		makeMove: function() {
			if(this.canPlay) {
				this.$parent.$parent.makeMove(this.q, this.r)
			}
		},
	},
	template: `<g>
		<hexagon :x="x" :y="y" :r="size" :fill="highlight" stroke="#555"/>

		<g v-if="char" style="isolation:isolate">
			<piece v-if="'Rmy'.includes(char)" char="R" :x="x" :y="y-pieceOffset*Math.sin(Math.PI/2)" :size="pieceSize" style="mix-blend-mode:screen"/>
			<piece v-if="'Yrg'.includes(char)" char="Y" :x="x+pieceOffset*Math.cos(Math.PI/6)" :y="y-pieceOffset*Math.sin(Math.PI/6)" :size="pieceSize" style="mix-blend-mode:multiply"/>
			<piece v-if="'Gyc'.includes(char)" char="G" :x="x+pieceOffset*Math.cos(11*Math.PI/6)" :y="y-pieceOffset*Math.sin(11*Math.PI/6)" :size="pieceSize" style="mix-blend-mode:screen"/>
			<piece v-if="'Cgb'.includes(char)" char="C" :x="x" :y="y-pieceOffset*Math.sin(3*Math.PI/2)" :size="pieceSize" style="mix-blend-mode:multiply"/>
			<piece v-if="'Bcm'.includes(char)" char="B" :x="x+pieceOffset*Math.cos(7*Math.PI/6)" :y="y-pieceOffset*Math.sin(7*Math.PI/6)" :size="pieceSize" style="mix-blend-mode:screen"/>
			<piece v-if="'Mbr'.includes(char)" char="M" :x="x+pieceOffset*Math.cos(5*Math.PI/6)" :y="y-pieceOffset*Math.sin(5*Math.PI/6)" :size="pieceSize" style="mix-blend-mode:multiply"/>
		</g>

		<circle v-if="canPlay" v-on:click="makeMove" :cx="x" :cy="y" :r="size*0.8" stroke="none" fill="hsl(0, 100%, 100%, 1%)" style="cursor:pointer"/>
	</g>`
})

Vue.component('hexagon', {
	delimiters: ['[[', ']]'],
	props: ['x', 'y', 'r', 'fill', 'stroke'],
	computed: {
		points: function() {
			var pts = [
				[this.x, this.y - this.r * Math.sin(Math.PI/2)],
				[this.x + this.r * Math.cos(Math.PI/6), this.y - this.r * Math.sin(Math.PI/6)],
				[this.x + this.r * Math.cos(11*Math.PI/6), this.y - this.r * Math.sin(11*Math.PI/6)],
				[this.x, this.y - this.r*Math.sin(3*Math.PI/2)],
				[this.x + this.r * Math.cos(7*Math.PI/6), this.y - this.r * Math.sin(7*Math.PI/6)],
				[this.x + this.r * Math.cos(5*Math.PI/6), this.y - this.r * Math.sin(5*Math.PI/6)],
			]

			var out = ""
			for(i in pts) {
				out += pts[i][0] + ',' + pts[i][1] + ' '
			}
			return out
		},
	},
	template: `<g>
		<polygon :points="points" :fill="fill" :stroke="stroke" stroke-width="0.8"/>
	</g>`
})

Vue.component('piece', {
	mixins: [colorMixin],
	delimiters: ['[[', ']]'],
	props: ['x', 'y', 'size', 'char'],
	computed: {
		color: function() { return this.colors[this.char].normal },
		multiplier: function() {
			return 1
			return (store.getters.currentColor == this.char ? 1.2 : 1)
		},
		stroke: function() {
			return 'none'
			return (store.getters.currentColor == this.char ? '#333' : 'none')
		},
	},
	template: `<g>
		<circle :cx="x" :cy="y" :r="size * multiplier" :fill="color" :stroke="stroke" stroke-width="0.5"/>
		<g v-if="false && stroke!='none'">
			<circle :cx="x" :cy="y" :r="size * multiplier * 0.95" fill="none" stroke="#eee" stroke-width="0.3"/>
			<circle :cx="x" :cy="y" :r="size * multiplier * 0.9" fill="none" stroke="#333" stroke-width="0.3"/>
		</g>
	</g>`
})

Vue.component('logo', {
	mixins: [colorMixin],
	delimiters: ['[[', ']]'],
	props: ['x', 'y', 'size'],
	methods: {
		hexagonPoints: function(size) {
			var piThirds = Math.PI / 3
			var pts = []
			for(i = 2; i >= -4; i--) {
				pts.push([
					this.x + size * Math.cos(i * piThirds),
					this.y - size * Math.sin(i * piThirds),
				])
			}
			return pts
		},
		polygonPoints: function(i) {
			var bigHexPts = this.hexagonPoints(this.size)
			var smallHexPts = this.hexagonPoints(this.size * 2/3)

			var pts = [bigHexPts[i % 6].join(','), bigHexPts[(i+1) % 6].join(','), smallHexPts[(i+1) % 6].join(','), smallHexPts[i % 6].join(',')]
			return pts.join(' ')
		},
	},
	template: `<g>
		<polygon :points="polygonPoints(0)" :fill="colors.R.normal"/>
		<polygon :points="polygonPoints(1)" :fill="colors.Y.normal"/>
		<polygon :points="polygonPoints(2)" :fill="colors.G.normal"/>
		<polygon :points="polygonPoints(3)" :fill="colors.C.normal"/>
		<polygon :points="polygonPoints(4)" :fill="colors.B.normal"/>
		<polygon :points="polygonPoints(5)" :fill="colors.M.normal"/>

		<line :x1="hexagonPoints(size)[0][0]" :y1="hexagonPoints(size)[0][1]" :x2="hexagonPoints(size)[3][0]" :y2="hexagonPoints(size)[3][1]" stroke="#fff" :stroke-width="size/10"/>
		<line :x1="hexagonPoints(size)[1][0]" :y1="hexagonPoints(size)[1][1]" :x2="hexagonPoints(size)[4][0]" :y2="hexagonPoints(size)[4][1]" stroke="#fff" :stroke-width="size/10"/>
		<line :x1="hexagonPoints(size)[2][0]" :y1="hexagonPoints(size)[2][1]" :x2="hexagonPoints(size)[5][0]" :y2="hexagonPoints(size)[5][1]" stroke="#fff" :stroke-width="size/10"/>
	</g>`
})

Vue.component('color-picker', {
	mixins: [colorMixin],
	delimiters: ['[[', ']]'],
	computed: {
		variantLabel: function() {
			return this.teams.join(' ')
		},
		teams: function() {
			switch(store.getters.variant) {
				case 'MRY': return ['MRY', 'GCB']
				case 'RGB': return ['RGB', 'CMY']
				case 'MR': return ['MR', 'YG', 'CB']
				case 'RC': return ['RC', 'BY', 'GM']
				case 'R': return ['R', 'Y', 'G', 'C', 'B', 'M']
			}
		},
		myTeam: function() {
			for(team of this.teams) {
				for(color of team) {
					if(store.state.colorPlayers[color] == this.$parent.pid) return team
				}
			}
			return null
		},
	},
	methods: {
		isMine: function(color) { return store.state.colorPlayers[color] == this.$parent.pid },
		isClaimed: function(color) { return store.state.colorPlayers[color] },//.fix
		canClick: function(color, team) {
			if(this.isMine(color)) return true
			else if(this.isClaimed(color)) return false
			else return !this.myTeam || this.myTeam == team
		},
		toggleColor: function(color) {
			if(this.isMine(color)) {
				store.state.colorPlayers[color] = null
				this.$parent.releaseColor(color)
			} else {
				store.state.colorPlayers[color] = 'me'
				this.$parent.claimColor(color)
			}

			//.request color claim, which will broadcast all colors, then commit the state change there
		},
		icon: function(color) {
			if(this.isMine(color)) return 'fa-user-circle'
			else if(this.isClaimed(color)) return 'fa-check-circle'
			else return 'fa-circle'
		},
	},
	template: `<div>
		<div v-for="team in teams" :key="team.id" style="white-space:nowrap">
			<span
				v-for="color in team"
				:key="color.id"
				class="icon is-large"
				v-on:click="canClick(color,team) && toggleColor(color)"
				style="margin-right:0.5rem;"
				:style="'color:' + (myTeam&&team!=myTeam ? colors[color].light : colors[color].normal) + '; cursor:' + (canClick(color,team) ? 'pointer' : 'not-allowed')"
			>
				<i class="far fa-3x" :class="icon(color)"></i>
			</span>

			<hr style="margin: 0.5em 0">
		</div>


		<div style="text-align:left">
			<div><span class="icon"><i class="far fa-user-circle"></i></span>: Mine</div>
			<div><span class="icon"><i class="far fa-check-circle"></i></span>: Claimed</div>
			<div><span class="icon"><i class="far fa-circle"></i></span>: Unclaimed</div>
		</div>
	</div>`
})

Vue.component('move-browser', {
	mixins: [colorMixin],
	delimiters: ['[[', ']]'],
	data: function() {
		var moves = JSON.parse(document.getElementById('move-browser-moves').textContent)
		return {
			curIdx: null,
			moves: moves,
		}
	},
	beforeMount: function() {
		// prepend the initial state
		this.moves.unshift({hfen:'3/4/5/4/3 R ' + store.getters.variant})
		// show the last move on load
		this.last()
	},
	computed: {
		nrows: function() { return Math.ceil(this.moves.length / 6) },
		maxDigits: function() { return this.moves.length.toString().length },
	},
	methods: {
		setIdx: function(idx) {
			// Clamp to [0, length-1]
			idx = Math.min(Math.max(idx, 0), this.moves.length - 1)

			if(idx !== this.curIdx) {
				this.curIdx = idx
				store.commit('setHfen', this.moves[this.curIdx].hfen)
			}
		},
		first: function() { this.setIdx(0) },
		prev: function() { this.setIdx(this.curIdx - 1) },
		next: function() { this.setIdx(this.curIdx + 1) },
		last: function() { this.setIdx(this.moves.length - 1) },
	},
	template: `<div style="display:inline-block; text-align:center;">
		<span class="icon is-large" v-on:click="first" style="cursor:pointer"><i class="fas fa-2x fa-angle-double-left"></i></span>
		<span class="icon is-large" v-on:click="prev" v-on:keyup.left="prev" style="cursor:pointer"><i class="fas fa-2x fa-angle-left"></i></span>
		<span class="icon is-large" v-on:click="next" v-on:keyup.right="next" style="cursor:pointer"><i class="fas fa-2x fa-angle-right"></i></span>
		<span class="icon is-large" v-on:click="last" style="cursor:pointer"><i class="fas fa-2x fa-angle-double-right"></i></span>

		<div style=" font-family:'Lucida Console',Monaco,monospace; white-space:nowrap; text-align:left">
			<span v-for="(move, idx) in moves" v-if="idx>0">
				<span style="color:#aaa; font-size:0.6rem; margin-right:-0.4rem;">
					[[ idx.toString().padStart(maxDigits, '&nbsp;') ]].
				</span>
				<span v-on:click="setIdx(idx)" style="font-size:0.8rem; cursor:pointer;" :style="idx==curIdx ? 'background-color:'+colors['RYGCBM'[(idx-1)%6]].light : ''">
					[[ move.q >= 0 ? '+'+move.q : move.q ]][[ move.r >= 0 ? '+'+move.r : move.r ]]
				</span>

				<br v-if="idx % 6 == 0">
			</span>
		</div>
	</div>`
})


var app = new Vue({
	mixins: [colorMixin],
	delimiters: ['[[', ']]'],
	el: '#app',
	data: {
		socket: undefined,
		socket_is_live: false,
		pid: undefined,
		termination_message: null,
	},
	beforeMount: function() {
		this.colors.R.name = 'Red'
		this.colors.Y.name = 'Yellow'
		this.colors.G.name = 'Green'
		this.colors.C.name = 'Cyan'
		this.colors.B.name = 'Blue'
		this.colors.M.name = 'Magenta'

		if(IS_LIVE !== false) {
			var game_uid = JSON.parse(document.getElementById('GAMEUID').textContent)

			this.socket = new ReconnectingWebSocket('ws://' + window.location.hostname + ':8880/ws/play/' + game_uid + '/')
			this.socket.onopen = this.socket_opened
			this.socket.onclose = this.socket_closed
			this.socket.onmessage = this.socket_message
			this.socket.onerror = this.socket_error
		}
	},
	computed: {
		hfen: function() { return store.state.hfen },
		currentColor: function() { return store.getters.currentColor },
		colorPlayers: function() { return store.state.colorPlayers },
		isMyTurn: function() {
			return store.state.colorPlayers[this.currentColor] == this.pid
		},
	},
	methods: {
		socket_opened: function(e) {
			this.socket_is_live = true
			console.log("Connected to websocket")
		},
		socket_closed: function(e) {
			this.socket_is_live = false
			console.error("Disconnected from websocket")
		},
		socket_message: function(e) {
			var data = JSON.parse(e.data)
			console.log("Socket message", data)

			if(typeof data.pid !== 'undefined') this.pid = data.pid

			if(data.hfen) {
				store.commit('setHfen', data.hfen)
				if(data.move) {
					//.store to array?
				}
			}

			if(data.color_players) {
				store.commit('setColorPlayers', data.color_players)
			}

			if(typeof data.termination !== 'undefined') {
				store.commit('terminate')

				if(data.termination == 'DRAW') {
					this.termination_message = "DRAW"
				} else if('RYGCBM'.includes(data.termination)) {
					this.termination_message = this.colors[data.termination].name.toUpperCase() + " wins!"
				} else {
					this.termination_message = "GAME OVER"
				}
			}

			if(typeof data.error !== 'undefined') {
				switch(data.error) {
					case 'OUTDATED_HFEN':
						alert("You tried to submit a move for an outdated game state. If the board is not updated automatically, please refresh the page.")
						break
					case 'OUT_OF_TURN':
						alert("It is "+data.expected_color+"'s turn, not "+data.color+"'s.")
						break
					case 'NOT_YOUR_COLOR':
						alert("You do not control that color ("+data.color+").")
						break
					case 'GAME_OVER':
						alert("The game has terminated. You cannot make another move.")
						break
					case 'ILLEGAL_MOVE':
						alert("That is not a valid move.")
						break
					default:
						alert("ERROR: " + data.error)
						break
				}
			}
		},
		socket_error: function(e) {
			console.error("Socket error", e)
		},

		claimColor: function(color) {
			this.socket.send(JSON.stringify({
				'action': 'claim_color',
				'color': color,
			}))
		},
		releaseColor: function(color) {
			this.socket.send(JSON.stringify({
				'action': 'release_color',
				'color': color,
			}))
		},
		releaseAllColors: function() {
			this.socket.send(JSON.stringify({'action': 'release_all_colors'}))
		},

		makeMove: function(q, r) {
			this.socket.send(JSON.stringify({
				'action': 'make_move',
				'hfen': this.hfen,
				'color': this.currentColor,
				'q': q,
				'r': r,
			}))
		},

		test: function() {
			console.log('test')
			this.socket.close()
		},
	},
})
