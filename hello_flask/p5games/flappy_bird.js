var bird;
var pipes = [];
var score = 0;
var maxScore = 0;
var isOver = false;

function setup() {
  var canvas = createCanvas(400,600);
  canvas.parent('sketch-holder');
  bird = new Bird();
  pipes.push(new Pipe());
}

function draw() {
  background(0);

  bird.show();

  if (pipes[0].x == 140) {
    pipes.push(new Pipe());
  }

  for(var i = pipes.length - 1; i >= 0; i--) {
    pipes[i].show();
    pipes[i].update();

    if(pipes[i].pass(bird)) {
        score += 1;
    }

    if(pipes[i].hits(bird)) {
        gameover();
    }

    if(pipes[i].offscreen()){
        pipes.splice(i, 1);
    }

  }

  fill(66,185,104);
  rect(0, height-16, width, height);

  bird.update();
  showScores();
}

function showScores() {
  textSize(32);
  fill(170, 44, 160);
  text('score: ' + score, 5, 32);
  text('record: ' + maxScore, 5, 64);
}

function gameover() {
  textSize(64);
  textAlign(CENTER, CENTER);
  fill(170, 44, 160);
  text('GAMEOVER', width / 2, height / 2);
  textSize(32);
  text('press space to try again', width/2, height/2 + 48);
  textAlign(LEFT, BASELINE);
  maxScore = max(score, maxScore);
  isOver = true;
  noLoop();
}

function reset() {
  isOver = false;
  score = 0;
  pipes = [];

  pipes.push(new Pipe());

  bird = new Bird();
  loop();
}

function keyPressed() {
    if (key === ' ') {
        bird.up();
        if (isOver) reset();
    }
}

function Bird() {
    this.y = height/2;
    this.x = 64;
    this.radius = 32;

    this.gravity = 0.25;
    this.lift = -6;
    this.velocity = 0;

    this.show = function() {
        fill(244,223,66);
        ellipse(this.x, this.y, this.radius, this.radius);
    }

    this.up = function() {
        this.velocity = this.lift;
    }

    this.update = function() {
        this.velocity += this.gravity;
        this.y += this.velocity;

        if (this.y > height) {
            this.y = height;
            this.velocity = 0;
        }
        if (this.y < 0) {
            this.y = 0;
            this.velocity = 0;
        }

    }
}

function Pipe() {
    this.spacing = 150;
    this.top = random(height/8, height * 4 / 6);
    this.bottom = this.top + this.spacing;

    this.x = width;
    this.w = 64;
    this.speed = 2;

    this.passed = false;
    this.highlight = false;

    this.hits = function(bird) {
        var halfBird = bird.radius/2 - 3;
        if(bird.y-halfBird < this.top && bird.x+halfBird > this.x && bird.x-halfBird < this.x + this.w ||
            bird.y+halfBird > this.bottom && bird.x+halfBird > this.x && bird.x-halfBird < this.x + this.w || bird.y+halfBird > height-16) {
                this.highlight = true;
                return true;
        }
        return false;
    }

    this.pass = function(bird) {
        if(bird.x > this.x && !this.passed) {
            this.passed = true;
            return true;
        }
        return false;
    }

    this.show = function() {
        fill(66,244,104);
        if (this.highlight) {
            fill(255, 0, 0);
        }
        rect(this.x, 0, this.w, this.top);
        rect(this.x, this.bottom, this.w, height);
    }

    this.update = function() {
        this.x -= this.speed;
    }

    this.offscreen = function() {
        return(this.x < -this.w);
    }

}

