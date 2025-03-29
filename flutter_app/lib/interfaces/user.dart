class User {
  final String email;
  final String name;

  User({required this.email, required this.name});

  factory User.fromJson(Map<String, dynamic> json) {
    return switch (json) {
      {'email': String email, 'name': String name} => User(
        email: email,
        name: name,
      ),
      _ => throw const FormatException('Failed to load user.'),
    };
  }
}
