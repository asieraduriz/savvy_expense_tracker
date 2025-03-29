import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:savvy_expense_tracker/interfaces/user.dart';
import 'package:savvy_expense_tracker/services/auth.dart';

class AuthProvider extends ChangeNotifier {
  final AuthService authService;

  User? _user;
  String? _accessToken;

  AuthProvider({required this.authService});

  User? get user => _user;
  String? get accessToken => _accessToken;

  Future<void> signup(String name, String email, String password) async {
    final response = await authService.signup(name, email, password);
    if (response.statusCode == 201) {
      final decodedResponse = jsonDecode(response.body);
      _user = User.fromJson(decodedResponse);
      _accessToken = decodedResponse['access_token'];

      print(_user);
      print(_accessToken);
      notifyListeners();
    } else {
      throw Exception('Errror signing up user. ${response.body}');
    }
  }
}
