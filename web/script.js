function locomotive() {
  gsap.registerPlugin(ScrollTrigger);

  const locoScroll = new LocomotiveScroll({
    el: document.querySelector("#main"),
    smooth: true ,
  });
  locoScroll.on("scroll", ScrollTrigger.update);

  ScrollTrigger.scrollerProxy("#main", {
    scrollTop(value) {
      return arguments.length
        ? locoScroll.scrollTo(value, 0, 0)
        : locoScroll.scroll.instance.scroll.y;
    },

    getBoundingClientRect() {
      return {
        top: 0,
        left: 0,
        width: window.innerWidth,
        height: window.innerHeight,
      };
    },

    pinType: document.querySelector("#main").style.transform
      ? "transform"
      : "fixed",
  });
  ScrollTrigger.addEventListener("refresh", () => locoScroll.update());
  ScrollTrigger.refresh();
}
locomotive();

  // Robot animation: float/rotate loop + entrance when #page1 is reached
  (function(){
    const robot = document.getElementById('robot-img');
    const wrap = document.getElementById('robot-wrap');
    if(!robot || !wrap || !window.gsap) return;

    // entrance animation when #page1 enters view
    gsap.fromTo(wrap, {opacity:0, y:30, scale:0.95}, {
      opacity:1,
      y:0,
      scale:1,
      duration: 0.9,
      ease: 'power2.out',
      scrollTrigger: {
        trigger: '#page1',
        scroller: '#main',
        start: 'top center',
        // markers: true
      }
    });

    // gentle floating + subtle rotation loop for the robot image
    gsap.to(robot, {
      y: -18,
      rotation: 3,
      duration: 2.6,
      ease: 'sine.inOut',
      yoyo: true,
      repeat: -1
    });

  })();

const canvas = document.querySelector("canvas");
const context = canvas.getContext("2d");

canvas.width = window.innerWidth;
canvas.height = window.innerHeight;


window.addEventListener("resize", function () {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  render();
});

function files(index) {
  var data = `
     ./Img/male0001.png
     ./Img/male0002.png
     ./Img/male0003.png
     ./Img/male0004.png
     ./Img/male0005.png
     ./Img/male0006.png
     ./Img/male0007.png
     ./Img/male0008.png
     ./Img/male0009.png
     ./Img/male0010.png
     ./Img/male0011.png
     ./Img/male0012.png
     ./Img/male0013.png
     ./Img/male0014.png
     ./Img/male0015.png
     ./Img/male0016.png
     ./Img/male0017.png
     ./Img/male0018.png
     ./Img/male0019.png
     ./Img/male0020.png
     ./Img/male0021.png
     ./Img/male0022.png
     ./Img/male0023.png
     ./Img/male0024.png
     ./Img/male0025.png
     ./Img/male0026.png
     ./Img/male0027.png
     ./Img/male0028.png
     ./Img/male0029.png
     ./Img/male0030.png
     ./Img/male0031.png
     ./Img/male0032.png
     ./Img/male0033.png
     ./Img/male0034.png
     ./Img/male0035.png
     ./Img/male0036.png
     ./Img/male0037.png
     ./Img/male0038.png
     ./Img/male0039.png
     ./Img/male0040.png
     ./Img/male0041.png
     ./Img/male0042.png
     ./Img/male0043.png
     ./Img/male0044.png
     ./Img/male0045.png
     ./Img/male0046.png
     ./Img/male0047.png
     ./Img/male0048.png
     ./Img/male0049.png
     ./Img/male0050.png
     ./Img/male0051.png
     ./Img/male0052.png
     ./Img/male0053.png
     ./Img/male0054.png
     ./Img/male0055.png
     ./Img/male0056.png
     ./Img/male0057.png
     ./Img/male0058.png
     ./Img/male0059.png
     ./Img/male0060.png
     ./Img/male0061.png
     ./Img/male0062.png
     ./Img/male0063.png
     ./Img/male0064.png
     ./Img/male0065.png
     ./Img/male0066.png
     ./Img/male0067.png
     ./Img/male0068.png
     ./Img/male0069.png
     ./Img/male0070.png
     ./Img/male0071.png
     ./Img/male0072.png
     ./Img/male0073.png
     ./Img/male0074.png
     ./Img/male0075.png
     ./Img/male0076.png
     ./Img/male0077.png
     ./Img/male0078.png
     ./Img/male0079.png
     ./Img/male0080.png
     ./Img/male0081.png
     ./Img/male0082.png
     ./Img/male0083.png
     ./Img/male0084.png
     ./Img/male0085.png
     ./Img/male0086.png
     ./Img/male0087.png
     ./Img/male0088.png
     ./Img/male0089.png
     ./Img/male0090.png
     ./Img/male0091.png
     ./Img/male0092.png
     ./Img/male0093.png
     ./Img/male0094.png
     ./Img/male0095.png
     ./Img/male0096.png
     ./Img/male0097.png
     ./Img/male0098.png
     ./Img/male0099.png
     ./Img/male0100.png
     ./Img/male0101.png
     ./Img/male0102.png
     ./Img/male0103.png
     ./Img/male0104.png
     ./Img/male0105.png
     ./Img/male0106.png
     ./Img/male0107.png
     ./Img/male0108.png
     ./Img/male0109.png
     ./Img/male0110.png
     ./Img/male0111.png
     ./Img/male0112.png
     ./Img/male0113.png
     ./Img/male0114.png
     ./Img/male0115.png
     ./Img/male0116.png
     ./Img/male0117.png
     ./Img/male0118.png
     ./Img/male0119.png
     ./Img/male0120.png
     ./Img/male0121.png
     ./Img/male0122.png
     ./Img/male0123.png
     ./Img/male0124.png
     ./Img/male0125.png
     ./Img/male0126.png
     ./Img/male0127.png
     ./Img/male0128.png
     ./Img/male0129.png
     ./Img/male0130.png
     ./Img/male0131.png
     ./Img/male0132.png
     ./Img/male0133.png
     ./Img/male0134.png
     ./Img/male0135.png
     ./Img/male0136.png
     ./Img/male0137.png
     ./Img/male0138.png
     ./Img/male0139.png
     ./Img/male0140.png
     ./Img/male0141.png
     ./Img/male0142.png
     ./Img/male0143.png
     ./Img/male0144.png
     ./Img/male0145.png
     ./Img/male0146.png
     ./Img/male0147.png
     ./Img/male0148.png
     ./Img/male0149.png
     ./Img/male0150.png
     ./Img/male0151.png
     ./Img/male0152.png
     ./Img/male0153.png
     ./Img/male0154.png
     ./Img/male0155.png
     ./Img/male0156.png
     ./Img/male0157.png
     ./Img/male0158.png
     ./Img/male0159.png
     ./Img/male0160.png
     ./Img/male0161.png
     ./Img/male0162.png
     ./Img/male0163.png
     ./Img/male0164.png
     ./Img/male0165.png
     ./Img/male0166.png
     ./Img/male0167.png
     ./Img/male0168.png
     ./Img/male0169.png
     ./Img/male0170.png
     ./Img/male0171.png
     ./Img/male0172.png
     ./Img/male0173.png
     ./Img/male0174.png
     ./Img/male0175.png
     ./Img/male0176.png
     ./Img/male0177.png
     ./Img/male0178.png
     ./Img/male0179.png
     ./Img/male0180.png
     ./Img/male0181.png
     ./Img/male0182.png
     ./Img/male0183.png
     ./Img/male0184.png
     ./Img/male0185.png
     ./Img/male0186.png
     ./Img/male0187.png
     ./Img/male0188.png
     ./Img/male0189.png
     ./Img/male0190.png
     ./Img/male0191.png
     ./Img/male0192.png
     ./Img/male0193.png
     ./Img/male0194.png
     ./Img/male0195.png
     ./Img/male0196.png
     ./Img/male0197.png
     ./Img/male0198.png
     ./Img/male0199.png
     ./Img/male0200.png
     ./Img/male0201.png
     ./Img/male0202.png
     ./Img/male0203.png
     ./Img/male0204.png
     ./Img/male0205.png
     ./Img/male0206.png
     ./Img/male0207.png
     ./Img/male0208.png
     ./Img/male0209.png
     ./Img/male0210.png
     ./Img/male0211.png
     ./Img/male0212.png
     ./Img/male0213.png
     ./Img/male0214.png
     ./Img/male0215.png
     ./Img/male0216.png
     ./Img/male0217.png
     ./Img/male0218.png
     ./Img/male0219.png
     ./Img/male0220.png
     ./Img/male0221.png
     ./Img/male0222.png
     ./Img/male0223.png
     ./Img/male0224.png
     ./Img/male0225.png
     ./Img/male0226.png
     ./Img/male0227.png
     ./Img/male0228.png
     ./Img/male0229.png
     ./Img/male0230.png
     ./Img/male0231.png
     ./Img/male0232.png
     ./Img/male0233.png
     ./Img/male0234.png
     ./Img/male0235.png
     ./Img/male0236.png
     ./Img/male0237.png
     ./Img/male0238.png
     ./Img/male0239.png
     ./Img/male0240.png
     ./Img/male0241.png
     ./Img/male0242.png
     ./Img/male0243.png
     ./Img/male0244.png
     ./Img/male0245.png
     ./Img/male0246.png
     ./Img/male0247.png
     ./Img/male0248.png
     ./Img/male0249.png
     ./Img/male0250.png
     ./Img/male0251.png
     ./Img/male0252.png
     ./Img/male0253.png
     ./Img/male0254.png
     ./Img/male0255.png
     ./Img/male0256.png
     ./Img/male0257.png
     ./Img/male0258.png
     ./Img/male0259.png
     ./Img/male0260.png
     ./Img/male0261.png
     ./Img/male0262.png
     ./Img/male0263.png
     ./Img/male0264.png
     ./Img/male0265.png
     ./Img/male0266.png
     ./Img/male0267.png
     ./Img/male0268.png
     ./Img/male0269.png
     ./Img/male0270.png
     ./Img/male0271.png
     ./Img/male0272.png
     ./Img/male0273.png
     ./Img/male0274.png
     ./Img/male0275.png
     ./Img/male0276.png
     ./Img/male0277.png
     ./Img/male0278.png
     ./Img/male0279.png
     ./Img/male0280.png
     ./Img/male0281.png
     ./Img/male0282.png
     ./Img/male0283.png
     ./Img/male0284.png
     ./Img/male0285.png
     ./Img/male0286.png
     ./Img/male0287.png
     ./Img/male0288.png
     ./Img/male0289.png
     ./Img/male0290.png
     ./Img/male0291.png
     ./Img/male0292.png
     ./Img/male0293.png
     ./Img/male0294.png
     ./Img/male0295.png
     ./Img/male0296.png
     ./Img/male0297.png
     ./Img/male0298.png
     ./Img/male0299.png
     ./Img/male0300.png
 `;
  return data.split("\n")[index];
}

const frameCount = 300;

const images = [];
const imageSeq = {
  frame: 1,
};

for (let i = 0; i < frameCount; i++) {
  const img = new Image();
  img.src = files(i);
  images.push(img);
}

gsap.to(imageSeq, {
  frame: frameCount - 1,
  snap: "frame",
  ease: `none`,
  scrollTrigger: {
    scrub: 0.15,
    trigger: `#page>canvas`,
    start: `top top`,
    end: `600% top`,
    scroller: `#main`,
  },
  onUpdate: render,
});

images[1].onload = render;

function render() {
  scaleImage(images[imageSeq.frame], context);
}

function scaleImage(img, ctx) {
  var canvas = ctx.canvas;
  var hRatio = canvas.width / img.width;
  var vRatio = canvas.height / img.height;
  var ratio = Math.max(hRatio, vRatio);
  var centerShift_x = (canvas.width - img.width * ratio) / 2;
  var centerShift_y = (canvas.height - img.height * ratio) / 2;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.drawImage(
    img,
    0,
    0,
    img.width,
    img.height,
    centerShift_x,
    centerShift_y,
    img.width * ratio,
    img.height * ratio
  );
}
ScrollTrigger.create({
  trigger: "#page>canvas",
  pin: true,
  // markers:true,
  scroller: `#main`,
  start: `top top`,
  end: `600% top`,
});



gsap.to("#page1",{
  scrollTrigger:{
    trigger:`#page1`,
    start:`top top`,
    end:`bottom top`,
    pin:true,
    scroller:`#main`
  }
})
gsap.to("#page2",{
  scrollTrigger:{
    trigger:`#page2`,
    start:`top top`,
    end:`bottom top`,
    pin:true,
    scroller:`#main`
  }
})
gsap.to("#page3",{
  scrollTrigger:{
    trigger:`#page3`,
    start:`top top`,
    end:`bottom top`,
    pin:true,
    scroller:`#main`
  }
})