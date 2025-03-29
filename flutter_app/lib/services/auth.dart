import 'dart:convert';

import 'package:http/http.dart' as http;

class AuthService {
  Future<http.Response> signup(
    String name,
    String email,
    String password,
  ) async {
    return http.post(
      Uri.parse('http://localhost:8000/auth/signup/'),
      headers: <String, String>{
        'Content-Type': 'application/json; charset=UTF-8',
      },
      body: jsonEncode(<String, String>{
        'name': name,
        'email': email,
        'password': password,
      }),
    );
  }

  Future<http.Response> login(String email, String password) async {
    return http.post(
      Uri.parse('http://localhost:8000/auth/login/'),
      headers: <String, String>{
        'Content-Type': 'application/json; charset=UTF-8',
      },
      body: jsonEncode(<String, String>{'email': email, 'password': password}),
    );
  }

  Future<void> logout() async {
    // Log out the user
  }
}
