(this.webpackJsonpmizaweb2=this.webpackJsonpmizaweb2||[]).push([[245,57],{137:function(e,n){e.exports=function(e){var n={variants:[e.COMMENT("--","$"),e.COMMENT(/\{-/,/-\}/,{contains:["self"]})]},i={className:"type",begin:"\\b[A-Z][\\w']*",relevance:0},s={begin:"\\(",end:"\\)",illegal:'"',contains:[{className:"type",begin:"\\b[A-Z][\\w]*(\\((\\.\\.|,|\\w+)\\))?"},n]};return{name:"Elm",keywords:["let","in","if","then","else","case","of","where","module","import","exposing","type","alias","as","infix","infixl","infixr","port","effect","command","subscription"],contains:[{beginKeywords:"port effect module",end:"exposing",keywords:"port effect module where command subscription exposing",contains:[s,n],illegal:"\\W\\.|;"},{begin:"import",end:"$",keywords:"import as exposing",contains:[s,n],illegal:"\\W\\.|;"},{begin:"type",end:"$",keywords:"type alias",contains:[i,s,{begin:/\{/,end:/\}/,contains:s.contains},n]},{beginKeywords:"infix infixl infixr",end:"$",contains:[e.C_NUMBER_MODE,n]},{begin:"port",end:"$",keywords:"port",contains:[n]},{className:"string",begin:"'\\\\?.",end:"'",illegal:"."},e.QUOTE_STRING_MODE,e.C_NUMBER_MODE,i,e.inherit(e.TITLE_MODE,{begin:"^[_a-z][\\w']*"}),n,{begin:"->|<-"}],illegal:/;/}}},627:function(e,n,i){!function e(){e.warned||(e.warned=!0,console.log('Deprecation (warning): Using file extension in specifier is deprecated, use "highlight.js/lib/languages/elm" instead of "highlight.js/lib/languages/elm.js"'))}(),e.exports=i(137)}}]);
//# sourceMappingURL=245.250ee1df.chunk.js.map