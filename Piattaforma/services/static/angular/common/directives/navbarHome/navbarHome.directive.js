(function () {

  angular
    .module('crowdsense')
    .directive('navbarhome', navbarHome);

  function navbarHome () {
    return {
      restrict: 'EA',
      templateUrl: '/static/angular/common/directives/navbarHome/navbarHome.template.html',
      controller: 'navbarCtrl as navvm'
    };
  }

})();