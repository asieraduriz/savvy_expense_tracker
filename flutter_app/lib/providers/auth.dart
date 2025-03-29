import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:savvy_expense_tracker/interfaces/user.dart';
import 'package:savvy_expense_tracker/services/auth.dart';

enum AuthStatus { unauthenticated, authenticating, authenticated }

class AuthProvider extends ChangeNotifier {
  AuthStatus _status = AuthStatus.unauthenticated;
  String? _errorMessage;
  final AuthService authService;

  User? _user;
  String? _accessToken;

  AuthProvider({required this.authService});

  AuthStatus get status => _status;
  String? get errorMessage => _errorMessage;
  User? get user => _user;
  String? get accessToken => _accessToken;

  Future<void> signup(String name, String email, String password) async {
    _status = AuthStatus.authenticating;
    notifyListeners();

    await Future.delayed(const Duration(seconds: 1));

    final response = await authService.signup(name, email, password);
    if (response.statusCode == 201) {
      final decodedResponse = jsonDecode(response.body);
      _user = User.fromJson(decodedResponse);
      _accessToken = decodedResponse['access_token'];
      _status = AuthStatus.authenticated;

      print(_user);
      print(_accessToken);
    } else {
      _status = AuthStatus.unauthenticated;
      _errorMessage = 'Errror signing up user. ${response.body}';
    }
    notifyListeners();
  }

  Future<void> login(String email, String password) async {
    _status = AuthStatus.authenticating;
    notifyListeners();

    await Future.delayed(const Duration(seconds: 1));

    final response = await authService.login(email, password);
    if (response.statusCode == 200) {
      final decodedResponse = jsonDecode(response.body);
      _user = User.fromJson(decodedResponse);
      _accessToken = decodedResponse['access_token'];
      _status = AuthStatus.authenticated;
      print(_user);
      print(_accessToken);
    } else {
      _status = AuthStatus.unauthenticated;
      _errorMessage = 'Errror login in user. ${response.body}';
    }
    notifyListeners();
  }

  void logout() {
    _status = AuthStatus.unauthenticated;
    _user = null;
    _accessToken = null;
    notifyListeners();
  }
}
