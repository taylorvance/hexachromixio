const store = new Vuex.Store({
	state: {
		hfen: '3/4/5/4/3 R MRY',
		myColors: [],
	},
	mutations: {
		setHfen: function(state, hfen) { state.hfen = hfen },
		setMyColors: function(state, colors) { state.myColors = colors },
	},
	getters: {
		currentColor: function(state) {
			return state.hfen.split(' ')[1]
		},
		mapRadius: function(state) {
			return (state.hfen.match(/\//g) || []).length / 2
		},
		isMyTurn: function(state, getters) {
			return state.myColors.includes(getters.currentColor)
		},
	},
})


var colorMixin = {
	data: function() {
		var colors = {}
		var hue = 0
		for(c of "RYGCBM") {
			colors[c] = {
				hsl: 'hsl('+hue+', 100%, 45%)',
				hslLight: 'hsl('+hue+', 75%, 75%)',
			}
			hue += 60
		}

		return {
			colors: colors,
		}
	},
}


Vue.component('board', {
	delimiters: ['[[', ']]'],
	props: ['x', 'y', 'size', 'hfen'],
	computed: {
		spaceSize: function() {
			return this.size / store.getters.mapRadius / 2.7
		},
		spaces: function() {
			var radius = store.getters.mapRadius
			var spaces = []

			var chars = store.state.hfen.split(' ')[0].replace(/(\d)/g, function(match) {
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
		/*
		function pointy_hex_to_pixel(hex):
		*/
	},
	template: `<g>
		<logo :x="x" :y="y" :size="size"/>

		<space v-for="space in spaces" :x="space.x" :y="space.y" :q="space.q" :r="space.r" :char="space.char" :size="spaceSize"/>
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
			if(store.getters.currentColor == 'R') {
				if(this.char=='' || 'rBG'.includes(this.char)) return true
			} else if(store.getters.currentColor == 'Y') {
				if(this.char=='' || 'yMC'.includes(this.char)) return true
			} else if(store.getters.currentColor == 'G') {
				if(this.char=='' || 'gRB'.includes(this.char)) return true
			} else if(store.getters.currentColor == 'C') {
				if(this.char=='' || 'cYM'.includes(this.char)) return true
			} else if(store.getters.currentColor == 'B') {
				if(this.char=='' || 'bGR'.includes(this.char)) return true
			} else if(store.getters.currentColor == 'M') {
				if(this.char=='' || 'mCY'.includes(this.char)) return true
			}

			return false
		},
		highlight: function() {
			if(this.canPlay) return this.colors[store.getters.currentColor].hslLight
			else return '#eee'
		},
		style: function() {
			if(!this.char) return ''
			else if('RGBcmy'.includes(this.char)) return 'mix-blend-mode:screen'
			else if('rgbCMY'.includes(this.char)) return 'mix-blend-mode:multiply'
		},
		curHue: function() {
			return {
				"R": 0,
				"Y": 60,
				"G": 120,
				"C": 180,
				"B": 240,
				"M": 300,
			}[store.getters.currentColor]
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

		<g style="isolation:isolate">
			<piece v-if="'Rmy'.includes(char)" :x="x" :y="y-pieceOffset*Math.sin(90 * Math.PI/180)" :size="pieceSize" :color="colors.R.hsl" :style="style"/>
			<piece v-if="'Yrg'.includes(char)" :x="x+pieceOffset*Math.cos(30*Math.PI/180)" :y="y-pieceOffset*Math.sin(30*Math.PI/180)" :size="pieceSize" :color="colors.Y.hsl" :style="style"/>
			<piece v-if="'Gyc'.includes(char)" :x="x+pieceOffset*Math.cos(330*Math.PI/180)" :y="y-pieceOffset*Math.sin(330*Math.PI/180)" :size="pieceSize" :color="colors.G.hsl" :style="style"/>
			<piece v-if="'Cgb'.includes(char)" :x="x" :y="y-pieceOffset*Math.sin(270*Math.PI/180)" :size="pieceSize" :color="colors.C.hsl" :style="style"/>
			<piece v-if="'Bcm'.includes(char)" :x="x+pieceOffset*Math.cos(210*Math.PI/180)" :y="y-pieceOffset*Math.sin(210*Math.PI/180)" :size="pieceSize" :color="colors.B.hsl" :style="style"/>
			<piece v-if="'Mbr'.includes(char)" :x="x+pieceOffset*Math.cos(150*Math.PI/180)" :y="y-pieceOffset*Math.sin(150*Math.PI/180)" :size="pieceSize" :color="colors.M.hsl" :style="style"/>
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
				[this.x, this.y - this.r * Math.sin(90*Math.PI/180)],
				[this.x + this.r * Math.cos(30*Math.PI/180), this.y - this.r * Math.sin(30*Math.PI/180)],
				[this.x + this.r * Math.cos(330*Math.PI/180), this.y - this.r * Math.sin(330*Math.PI/180)],
				[this.x, this.y - this.r*Math.sin(270*Math.PI/180)],
				[this.x + this.r * Math.cos(210*Math.PI/180), this.y - this.r * Math.sin(210*Math.PI/180)],
				[this.x + this.r * Math.cos(150*Math.PI/180), this.y - this.r * Math.sin(150*Math.PI/180)],
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
	delimiters: ['[[', ']]'],
	props: ['x', 'y', 'size', 'color'],
	template: `<g>
		<circle :cx="x" :cy="y" :r="size" :fill="color"/>
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
			for(i=1; i<=6; i++) {
				pts.push([
					this.x + size * -Math.cos(i * piThirds),
					this.y + size * -Math.sin(i * piThirds),
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
		<polygon :points="polygonPoints(0)" :fill="colors.R.hsl"/>
		<polygon :points="polygonPoints(1)" :fill="colors.Y.hsl"/>
		<polygon :points="polygonPoints(2)" :fill="colors.G.hsl"/>
		<polygon :points="polygonPoints(3)" :fill="colors.C.hsl"/>
		<polygon :points="polygonPoints(4)" :fill="colors.B.hsl"/>
		<polygon :points="polygonPoints(5)" :fill="colors.M.hsl"/>

		<line :x1="hexagonPoints(size)[0][0]" :y1="hexagonPoints(size)[0][1]" :x2="hexagonPoints(size)[3][0]" :y2="hexagonPoints(size)[3][1]" stroke="#fff" :stroke-width="size/10"/>
		<line :x1="hexagonPoints(size)[1][0]" :y1="hexagonPoints(size)[1][1]" :x2="hexagonPoints(size)[4][0]" :y2="hexagonPoints(size)[4][1]" stroke="#fff" :stroke-width="size/10"/>
		<line :x1="hexagonPoints(size)[2][0]" :y1="hexagonPoints(size)[2][1]" :x2="hexagonPoints(size)[5][0]" :y2="hexagonPoints(size)[5][1]" stroke="#fff" :stroke-width="size/10"/>
	</g>`
})


var app = new Vue({
	delimiters: ['[[', ']]'],
	el: '#app',
	data: {
		socket: undefined,
		socket_is_live: false,
		moves: [],
		colors: {
			'R': 'Red',
			'Y': 'Yellow',
			'G': 'Green',
			'C': 'Cyan',
			'B': 'Blue',
			'M': 'Magenta',
		},
	},
	beforeMount: function() {//.del this?
		this.socket = new ReconnectingWebSocket('ws://' + window.location.host + '/ws/play/' + game_uid + '/')
		this.socket.onopen = this.socket_opened
		this.socket.onclose = this.socket_closed
		this.socket.onmessage = this.socket_message
		this.socket.onerror = this.socket_error

		min = 1
		max = 100
		var n = Math.floor(Math.random() * (max - min) + min)

		this.moves = []
		for(i = 0; i < n; i++) {
			this.moves.push([
				Math.floor(Math.random() * 4 - 2),
				Math.floor(Math.random() * 4 - 2)
			])
		}
	},
	computed: {
		hfen: function() { return store.state.hfen },
		currentColor: function() { return store.getters.currentColor },
		moveDisplay: function() {
			var disp = ""
			var n_row = 1
			for(i in this.moves) {
				if(i % 6 == 0) {
					disp += "\n" + n_row + "."
					n_row++
				}
				var move = this.moves[i]
				disp += " "
				disp += (move[0] >= 0 ? "+" : "") + move[0]
				disp += (move[1] >= 0 ? "+" : "") + move[1]
			}
			return disp.substring(1)
		},
		hpgn: function() {
			var hpgn = ''
			hpgn += '[Variant "' + game_variant + '"]\n'
			hpgn += '\n' + this.moveDisplay
			return hpgn
		},
	},
	methods: {
		socket_opened: function(e) {
			this.socket_is_live = true
			console.log('Connected to websocket')
		},
		socket_closed: function(e) {
			this.socket_is_live = false
			console.error('Disconnected from websocket')
		},
		socket_message: function(e) {
			var data = JSON.parse(e.data)
			console.log('received socket message', data)

			if(data.hfen) store.commit('setHfen', data.hfen)

		},
		socket_error: function(e) {
			console.error("Socket error", e)
		},

		makeMove: function(q, r) {
			this.socket.send(JSON.stringify({
				'action': 'make_move',
				'color': this.currentColor,
				'q': q,
				'r': r,
			}))
		},

		test: function() {
			console.log('test')
		},
	},
})
