from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, RegisterUser, LoginForm, CommentForm
from flask_gravatar import Gravatar
from functools import wraps
import os
from datetime import datetime
import gunicorn




current_year = datetime.now().year

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)

# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sample.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# db.init_app(app)

gravatar = Gravatar(app, size=100, rating='g', default='retro', force_default=False, force_lower=False, use_ssl=False, base_url=None)


# CONFIGURE TABLES - creating one-to-many relationship
# parent
class BlogUsers(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(1000), nullable=False)
    # one to many bwn BlogUsers and BlogPost
    blog_post = relationship("BlogPost", back_populates="author")
    # one to many bwn BlogUsers and Comment
    user_comments = relationship("Comment", back_populates="user_commented")


# child
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)

    # relation between user and blog posts
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("BlogUsers", back_populates="blog_post")

    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    # one to many bwn BlogPost and Comment
    comments = relationship("Comment", back_populates="parent_post")


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)

    # relation between user and comment
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    # relation between post and comment
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))

    comment_text = db.Column(db.Text, nullable=False)

    user_commented = relationship("BlogUsers", back_populates="user_comments")
    parent_post = relationship("BlogPost", back_populates="comments")


# with app.app_context():
#     db.create_all()


# new_post = BlogPost(author="Saikumar Mujja",
#                     title="Weight gain diet plan Indian – 2500 calories",
#                     subtitle="The only diet plan you need to gain weight",
#                     date=datetime.now().strftime("%B %d, %Y"),
#                     body="What exactly is energy balance? Let me simply tell you."
#                          "Energy balance is nothing but calculating calorie in and calorie out properly."
#                          "If you are eating that means you are taking calories into your body (calorie in) and if you are burning calories through any physical activity that is calorie out."
#                          "weight gain diet plan"
#                          "If your calorie intake is equal to calorie out that means, you can not see the change in your weight – the weight will be constant."
#                          "If your calorie intake is less than the calories burned, that means you are eating less and"
#                          "If your calorie intake is more than the calories burned, then some energy lies within you and leads to gaining weight. "
#                          "However, the best weight gain diet plan given in this article will help you to gain weight.",
#                     img_url="https://www.themusclyadvisor.com/wp-content/uploads/2021/03/dukan-diet-1024x693.jpg")
# db.session.add(new_post)
# db.session.commit()


login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return BlogUsers.query.get(int(user_id))


def admin_only(f):
    @wraps(f)
    def access_denied(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)  # forbidden error
        return f(*args, **kwargs)
    return access_denied


@app.route('/')
def get_all_posts():
    # posts in ascending order
    # posts = BlogPost.query.all()

    # posts in desc order
    posts = db.session.query(BlogPost).order_by(BlogPost.id.desc()).all()
    return render_template("index.html", all_posts=posts, logged_in=current_user.is_authenticated, year=current_year)


@app.route('/register', methods=["POST", "GET"])
def register():
    user_register = RegisterUser()
    if user_register.validate_on_submit():
        if user_register.password.data != user_register.confirm_password.data:
            flash("Password does not match.")
            return redirect(url_for("register"))
        user_name = user_register.name.data
        user_email = user_register.email.data
        # check if user is existing
        if BlogUsers.query.filter_by(email=user_email).first():
            flash("You already signed up with this email. Login instead")
            return redirect(url_for('login'))

        user_password = generate_password_hash(user_register.password.data, method="pbkdf2:sha256", salt_length=8)
        new_user = BlogUsers(name=user_name,
                             email=user_email,
                             password=user_password)
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for("get_all_posts"))
    return render_template("register.html", form=user_register, logged_in=current_user.is_authenticated, year=current_year)


@app.route('/login', methods=["POST", "GET"])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        userEnteredEmail = login_form.email.data
        userEnteredPassword = login_form.password.data
        user = BlogUsers.query.filter_by(email=userEnteredEmail).first()
        # Email doesn't exist
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        # Password incorrect
        elif not check_password_hash(user.password, userEnteredPassword):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('get_all_posts'))
    return render_template("login.html", form=login_form, logged_in=current_user.is_authenticated, year=current_year)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=["Get", "POST"])
def show_post(post_id):
    comment_form = CommentForm()
    requested_post = BlogPost.query.get(post_id)
    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment")
            return redirect(url_for("login"))

        new_comment = Comment(author_id=current_user.id,
                              post_id=post_id,
                              comment_text=comment_form.comment.data)
        # user_commented=current_user,
        # parent_post=requested_post,
        # comment_text=comment_form.comment.data

        db.session.add(new_comment)
        db.session.commit()
        # return redirect(url_for("show_post"))

    return render_template("post.html", post=requested_post, logged_in=current_user.is_authenticated, form=comment_form, year=current_year)


@app.route("/about")
def about():
    return render_template("about.html", logged_in=current_user.is_authenticated, year=current_year)


@app.route("/contact")
def contact():
    return render_template("contact.html", logged_in=current_user.is_authenticated, year=current_year)


@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author_id=current_user.id,
            date=datetime.now().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form, logged_in=current_user.is_authenticated, is_edit=False)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author.name,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user.name
        post.body = edit_form.body.data
        db.session.commit()

    return render_template("make-post.html", form=edit_form, logged_in=current_user.is_authenticated, is_edit=True, year=current_year)


@app.route("/delete/<int:post_id>", methods=["GET", "POST"])
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/<int:current_post>/delete-comment/<int:comment_id>", methods=["Get", "POST"])
@admin_only
def delete_comment(comment_id, current_post):
    comment_form = CommentForm()
    current_post = BlogPost.query.get(current_post)
    comment_to_delete = Comment.query.get(comment_id)
    db.session.delete(comment_to_delete)
    db.session.commit()
    return render_template("post.html", post=current_post, logged_in=current_user.is_authenticated, form=comment_form, year=current_year)


if __name__ == "__main__":
    # app.run(debug=True)
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        # Start Gunicorn when the script is run using 'python app.py'
        from gunicorn.app.base import BaseApplication

        class FlaskGunicornApp(BaseApplication):
            def __init__(self, app, options=None):
                self.options = options or {}
                self.application = app
                super().__init__()

            def load_config(self):
                for key, value in self.options.items():
                    self.cfg.set(key, value)

            def load(self):
                return self.application

        gunicorn_options = {
            'bind': '0.0.0.0:8000',  # Specify your desired host and port
            'workers': 3,  # Adjust based on your server's capacity
            'timeout': 30,  # Set request timeout
        }

        FlaskGunicornApp(app, gunicorn_options).run()
    else:
        app.run(debug=True)

