var Display = {
    N2(num) {return (Array(2).join("0") + num).slice(-2);},
    datetime(d, with_hans, with_seconds){
        if(with_hans==undefined){with_hans=true}
        if(!d)return'';
        if(typeof d == 'string'){
            var date_str = d.replace(/-/g,"/").split('.')[0];
            d = new Date(date_str);
        }
        else if(typeof d == 'number'){
            d = new Date(parseInt(d)*1000);
        }

        if(!with_hans){
            var res = d.getFullYear()+'-'+Display.N2(d.getMonth()+1)+'-'+Display.N2(d.getDate()) +' '+ Display.N2(d.getHours())+':'+Display.N2(d.getMinutes())
            if(with_seconds){
                res += ':'+Display.N2(d.getSeconds())
            }
            return res
        }
        return d.getFullYear()+'年'+(d.getMonth()+1)+'月'+d.getDate()+'日 ' + Display.N2(d.getHours())+':'+Display.N2(d.getMinutes())
    },
    date(d, with_hans){
        if(with_hans==undefined){with_hans=true}
        if(!d)return'';
        if(typeof d == 'string'){
            var date_str = d.replace(/-/g,"/").split('.')[0];
            d = new Date(date_str);
        }
        else if(typeof d == 'number'){
            d = new Date(parseInt(d)*1000);
        }

        if(with_hans){
            return d.getFullYear()+'年'+(d.getMonth()+1)+'月'+d.getDate()+'日'
        }else{
            return d.getFullYear()+'-'+(d.getMonth()+1)+'-'+d.getDate()
        }
    },
    week_day(d){
        if(!d)return'';
        if(typeof d == 'string'){
            var date_str = d.replace(/-/g,"/").split('.')[0];
            d = new Date(date_str);
        }
        else if(typeof d == 'number'){
            d = new Date(parseInt(d)*1000);
        }
        return "日一二三四五六"[d.getDay()]
    },
    gender(v){
        switch(v){
            case "f":
                return '<i class="fa fa-venus"></i>'
            case "m":
                return '<i class="fa fa-mars"></i>'
            default:
                return '<i class="fa fa-mask"></i>'
        }
    },
    fen2yuan(val){
        return (val/100).toFixed(2)
    },
    f2y(val){
        return (val/100).toFixed(2)
    },
}