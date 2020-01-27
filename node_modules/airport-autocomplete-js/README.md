# Airport Autocomple JS 🛩

[![Build Status](https://travis-ci.org/konsalex/Airport-Autocomplete-JS.svg?branch=master)](https://travis-ci.org/konsalex/Airport-Autocomplete-JS) [![CocoaPods](https://img.shields.io/cocoapods/l/AFNetworking.svg)](https://github.com/konsalex/Airport-Autocomplete-JS) [![npm bundle size (minified)](https://img.shields.io/bundlephobia/min/airport-autocomplete-js.svg)](https://www.npmjs.com/package/airport-autocomplete-js)
[![semantic-release](https://img.shields.io/badge/%20%20%F0%9F%93%A6%F0%9F%9A%80-semantic--release-e10079.svg)](https://github.com/semantic-release/semantic-release)


## First airport autocomplete package for JS 🎉

After searching extensively I found out that there is not a single official repo for Aiport searching/autocompleting.

Now there is! Check it out, use it and give me some feedback 📨

## **Contents**

1. [Installation](#installation)
2. [Usage](#usage)
3. [Demo](#demo)
4. [Contribute](#contrib)
5. [Add Languages](#lang)
6. [News](#news)

## Intro 

This package depends on [Fuse.js](http://fusejs.io/) in order to search efficient the airports.json .

You can find the airports.json under the `src/data` folder. The data has being scrapped from [OpenFlights.org](https://openflights.org/data.html)

As you can see in the code in order to minimize the js size and serve it fast, the airport json is being fetched only when needed from [Github](https://raw.githubusercontent.com/konsalex/Airport-Autocomplete-JS/master/src/data/airports.json).

This package aims to be used in travel websites, flight claiming platforms and anywhere you would love to.

---

<a id="installation"></a>

## Installation 🐲

### Option 1: Node package

You can install it just by typing

```
npm -i airport-autocomplete-js
```

or if you have yarn

```
yarn add airport-autocomplete-js
```

### Option 2: Embed the script to your page

Just include the script in your page served by [jsDelivr](https://www.jsdelivr.com/) CDN

```
<script src="https://cdn.jsdelivr.net/npm/airport-autocomplete-js@latest/dist/index.browser.min.js"></script>
```

<a id="usage"></a>

## Usage 🌊

1. [Initialize](#init)
2. [Custom Styling / Formatting](#custom)

<a id="init"></a>

### Initialize

In order to use it just initialize instances of airport-autocomplete objects just by passing the input's id.

```
AirportInput("id-of-the-input-1")
AirportInput("id-of-the-input-n")

<!-- or give an options JS object in order to customize regarding your needs -->

AirportInput("id-of-the-input-n", options)
```

Regarding your needs, some of you may want to give bigger attention to IATA code search, others would love the City name search to gain the attention. So in addition to that, you can define your own options settings and pass it to the airport-autocomplete object.

```
const options = {
  fuse_options : {
      shouldSort: true,
      threshold: 0.4,
      maxPatternLength: 32,
      keys: [{
          name: "IATA",
          weight: 0.6
        },
        {
          name: "name",
          weight: 0.4
        },
        {
          name: "city",
          weight: 0.2
        }
      ]
    }
};

AirportInput("id-of-the-input-1", options)
```

For additional info on how fuse_option object works you can check Fuse.js well-documented website.

<a id="custom"></a>

### Stylying / Formatting 💅

You can style your Airport suggestions or even change the formatting of the output.

The **default** formatting is the following : 

`<div class="$(unique-result)" single-result" data-index="$(i)"> $(name) $(IATA) </br> $(city) ,$(country)</div>`

The formatting string parameters are listed below:

| Data        | Syntax           | Required  |
| ------------- |:-------------:| -----:|
| Unique ID     | $(unique-result) | `True` |
| Result Index    | data-index="$(i)" | `True` |
| Airport Name     | $(name) | `False` |
| Airport IATA code     | $(IATA) | `False` |
| Airport Country     | $(country) | `False` |
| Airport City     | $(city) | `False` |

Check the index.html in the demo folder for an example with the custom formatting.

---

<a id="demo"></a>

## Demo 📽

You can see it in action!

Clone the repo, install the dependencies and run `npm run dev` .

Then just open the `index.html` file inside demo folder and examine the code.

Here is a gif demonstrating the functionality.

![AirportJS demo](https://raw.githubusercontent.com/konsalex/Airport-Autocomplete-JS/master/assets/img/AirportJS_demo.gif)

---

<a id="contrib"></a>

## Contribute 🧪


Want to contribute? Just jump in and follow the instructions or open an issue and initialize a discussion on how to make this package better.

1. Install dependencies.

2. Run the dev script.

3. Open the index.html from `demo` folder and start testing and developing.

---

<a id="lang"></a>

## Languages 🗣

If you are writing a web app that needs to handle inputs from other languages I have a surprise for you.

You can enrich the airports.json with the names with your own language.

Check `src/data_scripts/addLanguage.py` and how it works.

As an input you have to provide a CSV (; delimeter) with the first column the names of your language, and the second the IATA code they represent in order to match them.

This code is working but we need to make it more robust and extensible.

Any recommendations are welcome!

<a id="news"></a>

## News

Changes:

1. Cleaned the aiport data, minimized International to Intl , removed 'Airport' as a word from the dataset.

2. Fixed double fetch of Airport Data, thanks @meeuwsen for noticing 🤟

3. Improved CSS styling 💅 and I need feedback from you to make new changes and make it even more dev friendly!

4. Added languages script, create data pull automated script (python), created a feature for custom styling/formatting .
