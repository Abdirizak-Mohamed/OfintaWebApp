$(document).ready(function() {
  var dashboardTable = $('.orders-table'),
      dashboardTableHead = dashboardTable.find('thead');

  dashboardTableHead.on('click', function () {
    window.location.href = $(this).data('url');
  })
});