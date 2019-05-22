// Create a plot with multiple traces
function plot_results(plot) {

  // List containing a trace for each time series
  var traces = [];

  var second_axis_present = false

  // Create a trace for each time series and add it to the list
  for (var key in plot.series) {
    var trace = {
      // The index is a string formatted array containing a timestamp as string,
      // these need to be packed as json, in order to be transmittable from the Python side to the JavaScript side
      x:JSON.parse(plot.index),
      y:plot.series[key].data,
      mode: 'lines',
      name: plot.series[key].name,
      line: {
        dash: 'solid',
        width: 3
      }
    };
    // Assign time series to second y axis, if it starts with "Temperature"
    if (plot.series[key].name.substring(0, 11) == 'Temperature') {
      trace.yaxis = 'y2';
      second_axis_present = true
    }
    traces.push(trace);
  }

  var layout = {
    title: plot.name,
    xaxis: {
      rangeselector: {buttons: [
          {
            label: 'Year',
            step: 'all'
          },
          /*
          {
            count: 1,
            label: 'First of month to date',
            step: 'month',
            stepmode: 'todate'
          },
          */
          {
            count: 30,
            label: 'Last 30 days',
            step: 'day',
            stepmode: 'backward'
          },
          {
            count: 7,
            label: 'Last 7 days',
            step: 'day',
            stepmode: 'backward'
          },
          {
            count: 3,
            label: 'Last 3 days',
            step: 'day',
            stepmode: 'backward'
          },
          {
            count: 2,
            label: 'Last 2 Days',
            step: 'day',
            stepmode: 'backward'
          },
        ]},
      //rangeslider: {range: ['2018-01-02', '2018-12-31']},
      range:['2018-01-02', '2018-12-31'],
      autorange: false,
      title:"Time",
      type:"datetime",
    },
    yaxis: {
      range: [-200., 5100.],
      autorange: true,
      title:'Power / Heat rate [W]'
    },
    legend: {
      x: 1.1,
      y: 0.5,
      traceorder: 'reversed',
      font: {
        size: 14
      }
    }
  };

  // If there are traces based on the second axis, add one to layout
  if (second_axis_present) {
    layout.yaxis2 = {
      title: 'Temperature [°C]',
      overlaying: 'y',
      side: 'right'
    }
  }

  Plotly.newPlot(plot.id, traces, layout, {scrollZoom:true}, {responsive: true});
}
