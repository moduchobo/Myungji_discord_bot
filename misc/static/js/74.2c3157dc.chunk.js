(this.webpackJsonpmizaweb2=this.webpackJsonpmizaweb2||[]).push([[74],{154:function(e,n){function a(e){return e?"string"===typeof e?e:e.source:null}function t(e){return function(){for(var e=arguments.length,n=new Array(e),t=0;t<e;t++)n[t]=arguments[t];return n.map((function(e){return a(e)})).join("")}("(?=",e,")")}function i(e){var n=arguments.length>1&&void 0!==arguments[1]?arguments[1]:{};return n.variants=e,n}e.exports=function(e){var n="[A-Za-z0-9_$]+",a=i([e.C_LINE_COMMENT_MODE,e.C_BLOCK_COMMENT_MODE,e.COMMENT("/\\*\\*","\\*/",{relevance:0,contains:[{begin:/\w+@/,relevance:0},{className:"doctag",begin:"@[A-Za-z]+"}]})]),r={className:"regexp",begin:/~?\/[^\/\n]+\//,contains:[e.BACKSLASH_ESCAPE]},s=i([e.BINARY_NUMBER_MODE,e.C_NUMBER_MODE]),l=i([{begin:/"""/,end:/"""/},{begin:/'''/,end:/'''/},{begin:"\\$/",end:"/\\$",relevance:10},e.APOS_STRING_MODE,e.QUOTE_STRING_MODE],{className:"string"});return{name:"Groovy",keywords:{built_in:"this super",literal:"true false null",keyword:"byte short char int long boolean float double void def as in assert trait abstract static volatile transient public private protected synchronized final class interface enum if else for while switch case break default continue throw throws try catch finally implements extends new import package return instanceof"},contains:[e.SHEBANG({binary:"groovy",relevance:10}),a,l,r,s,{className:"class",beginKeywords:"class interface trait enum",end:/\{/,illegal:":",contains:[{beginKeywords:"extends implements"},e.UNDERSCORE_TITLE_MODE]},{className:"meta",begin:"@[A-Za-z]+",relevance:0},{className:"attr",begin:n+"[ \t]*:",relevance:0},{begin:/\?/,end:/:/,relevance:0,contains:[a,l,r,s,"self"]},{className:"symbol",begin:"^[ \t]*"+t(n+":"),excludeBegin:!0,end:n+":",relevance:0}],illegal:/#|<\//}}}}]);
//# sourceMappingURL=74.2c3157dc.chunk.js.map