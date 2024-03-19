function $toast(content, time, callback) {
    let css = {
       padding: '5px 10px',
       fontSize: '16px',
       background: 'rgba(0,0,0,0.7)',
       color: '#fff',
       borderRadius: '6px',
       position: 'fixed',
       visibility: 'hidden',
       zIndex: 10000,
       maxWidth: '80vw',
    }
    time = time || 1400;
    let el = document.createElement('div');
    el.innerHTML=content;
    for(let attr in css){
        el.style[attr] = css[attr];
    }
    document.body.appendChild(el);
    let el_style = window.getComputedStyle(el);

    let h = parseInt(el_style.height.split('px')[0]);
    let w = parseInt(el_style.width.split('px')[0]);

    el.style.top = `calc(50vh - ${parseInt(h/2)}px)`;
    el.style.left = `calc(50vw - ${parseInt(w/2)}px)`;
    el.style.visibility = 'visible';

    setTimeout(function(){
       document.body.removeChild(el);
       callback && callback()
    }, time);
}


function $sticky(el_selector, wapper_selector){
   let $el = document.querySelector(el_selector)
   let top = $el.offsetTop
   let style = null

   document.querySelector(wapper_selector).addEventListener('scroll', e=>{

       if(e.target.scrollTop>top){
           if(style==null){
   
               style = {
                   position: $el.style.position,
                   top: $el.style.top,
                   left: $el.style.left,
               }
               $el.style.position='fixed'
               $el.style.top='0'
               $el.style.left=$el.offsetLeft+'px'

           }
       }else{
           for(let k in style){
               $el.style[k]=style[k]
           }
           style=null
       }
   })        

}

function $reLogin(confirm){
    let dom = document.getElementById("id_relogin")
    if(confirm===true){
      System.login.set(null)
      try{ menu.show(false) }catch(_){}
      try{ main.reset_page('login') }catch(_){}

      dom.className = 'dialog'
    }else{
      if(confirm){
        dom.querySelector('.body').innerHTML = confirm
        dom.className += ' active'
      }
    }
  }
