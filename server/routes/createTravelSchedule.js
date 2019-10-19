const express = require('express')
const path = require('path')
const bodyParser = require('body-parser')
const travelCostMinimizerRootPath = '../'

var router = express.Router()
/*
let runScript = new Promise(() => {
	const { spawn } = require('child_process')
	const pythonScript = spawn('python', [travelCostMinimizerRootPath + 'testScript.py'])//'travelCostMinimizer.py'])

	pythonScript.stdout.on('data', (data) => {
		console.log(data.toString())
	})
})

router.get('/', function(req, res){
	res.write('welcome\n')

	runScript.then((result) => {
		res.end(result)
	})
})
*/
router.use(
	bodyParser.urlencoded({
		extended: true
	})
)
router.use(bodyParser.json())

router.get('/', function(req, res){
	const { spawn } = require('child_process')
	const opt = {
		cwd: path.join(__dirname, '../../')
	}
	// inputs to python script
	// // validation occurs on the script itself
	const origins = JSON.stringify(req.body.origins)
	const destinations = JSON.stringify(req.body.destinations)
	const fixed_trips = JSON.stringify(req.body.fixed_trips)
	const travel_dates = JSON.stringify(req.body.travel_dates)
	const depart_time_start = req.body.depart_time_start
	const depart_time_end = req.body.depart_time_end
	const max_stopover_min = req.body.max_stopover_min
	const max_number_stops = req.body.max_number_stops
	const currency_choice = req.body.currency_choice
	const pythonScript = spawn('venv/bin/python3', 
		[
			path.join(__dirname, '../../onlineMinimizer.py'),
			origins,
			destinations,
			fixed_trips,
			travel_dates,
			depart_time_start,
			depart_time_end,
			max_stopover_min,
			max_number_stops,
			currency_choice
		], opt)
	
	pythonScript.stdout.on('data', (data) => {
		res.write(data)
	})

	pythonScript.stderr.on('data', (errData) => {
		res.write(errData)
	})

	pythonScript.on('error', (err) => {
		res.write(err)
	})

	pythonScript.on('exit', (code, signal) => {
		res.end('End')
	})
})


//export this router to use in our index.js
module.exports = router
