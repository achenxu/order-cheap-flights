var express = require('express')
var app = express()

var createTravelSchedule = require('./routes/createTravelSchedule.js')

app.use('/travel-schedule', createTravelSchedule)

app.listen(3000)

