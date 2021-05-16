/*
    jQuery for MaterializeCSS initialization
*/

$(document).ready(function () {
    $(".sidenav").sidenav({edge: "right"});
    $('.parallax').parallax();
    $('select').formSelect();
    $('.datepicker').datepicker({
        format: "dd mmmm, yyyy",
        yearRange: 2,
        showClearBtn: true,
        i18n: {
            done: "Select"
        }
    });
    $('.timepicker').timepicker({
        duration: 60,
        twelveHour: false,
        defaultTime: '12:00',
        showClearBtn: true,
        i18n: {
            done: "Select",
            cancel: "Cancel",
            clear: "Clear"
        }
    })
});