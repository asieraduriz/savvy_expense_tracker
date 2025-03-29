import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:savvy_expense_tracker/providers/auth.dart';

class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    final user = Provider.of<AuthProvider>(context, listen: false).user!;
    return Scaffold(
      appBar: AppBar(),
      body: Center(child: Text("Hello, ${user.name}")),
    );
  }
}
