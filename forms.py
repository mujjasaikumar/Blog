from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, EmailField
from wtforms.validators import DataRequired, URL, Email
from flask_ckeditor import CKEditorField


# WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


class RegisterUser(FlaskForm):
    name = StringField(label="Full Name", validators=[DataRequired()], render_kw={"placeholder": "Enter your Full name"})
    email = StringField(label="Email", validators=[DataRequired(), Email()], render_kw={"placeholder": "Enter your email"})
    password = PasswordField(label="Please enter password", validators=[DataRequired()], render_kw={"placeholder": "password > 8 chars"})
    confirm_password = StringField(label="Confirm password", validators=[DataRequired()], render_kw={"placeholder": "confirm your password"})
    submit = SubmitField(label="Sign me up")


class LoginForm(FlaskForm):
    email = StringField(label="Email", validators=[DataRequired(), Email()], render_kw={"placeholder": "Enter your email"})
    password = PasswordField(label="Please enter password", validators=[DataRequired()], render_kw={"placeholder": "Enter your password"})
    submit = SubmitField(label="log me up")


class CommentForm(FlaskForm):
    comment = CKEditorField("COMMENT", validators=[DataRequired()])
    submit = SubmitField(label="Submit comment")
