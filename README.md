# order-cheap-flights
Python script to find the cheapest flight plan for study abroad students.

## How It Works
The program works by taking in several parameters including:
  -date ranges that you are available to travel
  -airports (cities) that you could feasibly depart from
  -destinations (cities) that you would like to go
  -currency that you would like the prices reported in
  -trips that you are set on taking (fixed trips *explained below*)
  -maximum number of stops (layovers)
  -maximum amount of time each stop (layover)
  -starting and ending time of day to depart (specified as a range)
  
The program takes all of these parameters above and retrieves the cheapest flight for each combination of departure location, destination, and date range. It then totals the prices for all possible combinations of trips taken to build a schedule.

## Example Usage
For instance:
You are free for three weekends in November. You enter in all three weekends as date ranges. Next, you enter in 1 or more destinations you would like to go to on these three weekends. 
If only one destination is entered, it will print out the cheapest weekend to travel (round-trip), the price, and the URL. 
If more than one destination is entered, it will order the destinations into the weekends. For example, if the user wanted to attend Barcelona, Paris, and Rome, it would tell the user which order to attend the three would be the cheapest by comparing the total price of the following:

  Weekend 1 -> Barcelona, Weekend 2 -> Paris,     Weekend 3 -> Rome       >>>>> $XXX
  Weekend 1 -> Barcelona, Weekend 2 -> Rome,      Weekend 3 -> Paris      >>>>> $XXX
  Weekend 1 -> Paris,     Weekend 2 -> Barcelona, Weekend 3 -> Rome       >>>>> $XXX
  Weekend 1 -> Paris,     Weekend 2 -> Rome,      Weekend 3 -> Barcelona  >>>>> $XXX
  Weekend 1 -> Rome,      Weekend 2 -> Barcelona, Weekend 3 -> Paris      >>>>> $XXX
  Weekend 1 -> Rome,      Weekend 2 -> Paris,     Weekend 3 -> Barcelona  >>>>> $XXX
  
If more destinations are entered than the number of date ranges available, it will still take all destinations into consideration. The final output however will (obviously) have only as many destinations as available date ranges.
If the user has friends going to Paris on Weekend 2, the user could "fix" this trip and the possible schedules that would be compared are:
  Weekend 1 -> Barcelona, Weekend 2 -> Paris,     Weekend 3 -> Rome       >>>>> $XXX
  Weekend 1 -> Rome,      Weekend 2 -> Paris,     Weekend 3 -> Barcelona  >>>>> $XXX
Only the cheaper of the two options listed above would be printed to the user as well as the google flights URL to book each flight.
