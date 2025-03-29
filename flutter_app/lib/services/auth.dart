import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

class AuthService {
  late String baseUrl;

  AuthService() {
    baseUrl =
        Platform.isAndroid ? 'http://10.0.2.2:8000' : 'http://localhost:8000';
  }

  Future<http.Response> signup(
    String name,
    String email,
    String password,
  ) async {
    return http.post(
      Uri.parse('$baseUrl/auth/signup/'),
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
      Uri.parse('$baseUrl/auth/login/'),
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
