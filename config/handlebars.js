const Handlebars = require('handlebars/runtime');

function register(package) {

    for (var name in package) {
        Handlebars.registerHelper(name, package[name]);
    }

}

register(require('just-handlebars-helpers/lib/helpers/conditionals'));
register(require('just-handlebars-helpers/lib/helpers/math'));

Handlebars.registerHelper("fixed", (value, decimals) => { return (value).toFixed(decimals); } );

Handlebars.registerHelper("icon", (icon) => { return '<i class="bi bi-'+ icon + '"> </i>';  } );

Handlebars.registerHelper("makeid", (name) => { return name.toLowerCase().replace(/[^_0-9a-z]/gi, '_'); } );


/**
 * Handlebars runtime with custom helpers.
 * Used by handlebars-loader.
 */
module.exports = Handlebars;
