//extension boards and radio sockets
          String row_socket="", row_board0="", row_board1="", row_board2="", row_board3="", row_board4="";

          String in_ext0[]={"","","","","","","",""};
          String in_ext0_activate[]={"","","","","","","",""};
          String in_ext1[]={"","","","","","","",""};
          String in_ext2[]={"","","","","","","",""};
          String in_ext3[]={"","","","","","","",""};
          String in_ext4[]={"","","","","","","",""};

          String out_ext0[]={"","","","","","","",""};
          String out_ext0_activate[]={"","","","","","","",""};
          String out_ext1[]={"","","","","","","",""};
          String out_ext2[]={"","","","","","","",""};
          String out_ext3[]={"","","","","","","",""};
          String out_ext4[]={"","","","","","","",""};

          String socket_blk1[]={"","","","","","","",""};
          String socket_blk2[]={"","","","","","","",""};
          String socket_blk3[]={"","","","","","","",""};
          String socket_blk4[]={"","","","","","","",""};

          if (num_fields>36){
   try {
       //00000800
       row_socket=requestParts[35];

       if (row_socket.length()>=8)
       {
           try {

               //blk1
               state=hexToBin(row_socket.substring(0,2));
               state=Bin_8bits(state);
               for (int i=0; i<8; i++){
        socket_blk1[i]=state.substring(7-i,8-i);
               }

               //blk2
               state=hexToBin(row_socket.substring(2,4));
               state=Bin_8bits(state);
               for (int i=0; i<8; i++){
        socket_blk2[i]=state.substring(7-i,8-i);
               }

               //blk3
               state=hexToBin(row_socket.substring(4,6));
               state=Bin_8bits(state);
               for (int i=0; i<8; i++){
        socket_blk3[i]=state.substring(7-i,8-i);
               }

               //blk4
               state=hexToBin(row_socket.substring(6,8));
               state=Bin_8bits(state);
               for (int i=0; i<8; i++){
        socket_blk4[i]=state.substring(7-i,8-i);
               }

           }catch (Exception ex) {}
       }

   }catch (Exception ex) {}
          }

          if (num_fields>35){
   try {
       //800055000000
       row_board0=requestParts[34];
       //ext0
       if (row_board0.length()>=8)
       {
           try {

           //outputs ext0 activate
               state=hexToBin(row_board0.substring(10,12));
               state=Bin_8bits(state);
               for (int i=0; i<8; i++){
         out_ext0_activate[i]=state.substring(7-i,8-i);
               }

               //inputs ext0 activate
               state=hexToBin(row_board0.substring(8,10));
               state=Bin_8bits(state);
               for (int i=0; i<8; i++){
         in_ext0_activate[i]=state.substring(7-i,8-i);
               }

               //outputs state
               state=hexToBin(row_board0.substring(6,8));
               state=Bin_8bits(state);
               for (int i=0; i<8; i++){
         out_ext0[i]=state.substring(7-i,8-i);
               }

               //input1..4 state
               state=hexToBin(row_board0.substring(4,6));
               state=Bin_8bits(state);
               for (int i=0; i<4; i++){
         if (state.substring(6-i*2,8-i*2).equals("00")) in_ext0[i]="0";
         if (state.substring(6-i*2,8-i*2).equals("01")) in_ext0[i]="1";
         if (state.substring(6-i*2,8-i*2).equals("10")) in_ext0[i]="2";
         if (state.substring(6-i*2,8-i*2).equals("11")) in_ext0[i]="3";
               }

               //input5..8 state
               state=hexToBin(row_board0.substring(2,4));
               state=Bin_8bits(state);
               for (int i=0; i<4; i++){
         if (state.substring(6-i*2,8-i*2).equals("00")) in_ext0[i+4]="0";
         if (state.substring(6-i*2,8-i*2).equals("01")) in_ext0[i+4]="1";
         if (state.substring(6-i*2,8-i*2).equals("10")) in_ext0[i+4]="2";
         if (state.substring(6-i*2,8-i*2).equals("11")) in_ext0[i+4]="3";
               }

           }catch (Exception ex) {}
       }

   }catch (Exception ex) {}
          }

          if (num_fields>34){
   try {
   //80005500
   row_board1=requestParts[30];
   row_board2=requestParts[31];
   row_board3=requestParts[32];
   row_board4=requestParts[33];

   //ext1
   if (row_board1.length()>=8)
   {
   try {
   state=hexToBin(row_board1.substring(0,2));
           state=Bin_8bits(state);
           String board_type=state.substring(6,8);
   String input_2_zone=state.substring(2,6);

   //outputs state
   state=hexToBin(row_board1.substring(6,8));
           state=Bin_8bits(state);
   for (int i=0; i<8; i++){
   if ( (board_type.equals("00") && (i < 4)) || board_type.equals("01") )
   {
   out_ext1[i]=state.substring(7-i,8-i);
   }
   }

   //input1..4 state
   state=hexToBin(row_board1.substring(4,6));
           state=Bin_8bits(state);
   for (int i=0; i<4; i++){
   if ( board_type.equals("00") || board_type.equals("10") )
   {
   if (state.substring(6-i*2,8-i*2).equals("00")) in_ext1[i]="0";
   if (state.substring(6-i*2,8-i*2).equals("01")) in_ext1[i]="1";
   if (state.substring(6-i*2,8-i*2).equals("10")) in_ext1[i]="2";
   if (state.substring(6-i*2,8-i*2).equals("11")) in_ext1[i]="3";
   }
   }

   //input5..8 state
   state=hexToBin(row_board1.substring(2,4));
           state=Bin_8bits(state);
   for (int i=0; i<4; i++){
   if ( (board_type.equals("00") && input_2_zone.substring(3-i, 4-i).equals("1")) || board_type.equals("10") )
   {
   if (state.substring(6-i*2,8-i*2).equals("00")) in_ext1[i+4]="0";
   if (state.substring(6-i*2,8-i*2).equals("01")) in_ext1[i+4]="1";
   if (state.substring(6-i*2,8-i*2).equals("10")) in_ext1[i+4]="2";
   if (state.substring(6-i*2,8-i*2).equals("11")) in_ext1[i+4]="3";
   }
   }

   }catch (Exception ex) {}
   }

   //ext2
   if (row_board2.length()>=8)
   {
   try {
   state=hexToBin(row_board2.substring(0,2));
           state=Bin_8bits(state);
           String board_type=state.substring(6,8);
   String input_2_zone=state.substring(2,6);

   //outputs state
   state=hexToBin(row_board2.substring(6,8));
           state=Bin_8bits(state);
   for (int i=0; i<8; i++){
   if ( (board_type.equals("00") && (i < 4)) || board_type.equals("01") )
   {
   out_ext2[i]=state.substring(7-i,8-i);
   }
   }

   //input1..4 state
   state=hexToBin(row_board2.substring(4,6));
           state=Bin_8bits(state);
   for (int i=0; i<4; i++){
   if ( board_type.equals("00") || board_type.equals("10") )
   {
   if (state.substring(6-i*2,8-i*2).equals("00")) in_ext2[i]="0";
   if (state.substring(6-i*2,8-i*2).equals("01")) in_ext2[i]="1";
   if (state.substring(6-i*2,8-i*2).equals("10")) in_ext2[i]="2";
   if (state.substring(6-i*2,8-i*2).equals("11")) in_ext2[i]="3";
   }
   }

   //input5..8 state
   state=hexToBin(row_board2.substring(2,4));
           state=Bin_8bits(state);
   for (int i=0; i<4; i++){
   if ( (board_type.equals("00") && input_2_zone.substring(3-i, 4-i).equals("1")) || board_type.equals("10") )
   {
   if (state.substring(6-i*2,8-i*2).equals("00")) in_ext2[i+4]="0";
   if (state.substring(6-i*2,8-i*2).equals("01")) in_ext2[i+4]="1";
   if (state.substring(6-i*2,8-i*2).equals("10")) in_ext2[i+4]="2";
   if (state.substring(6-i*2,8-i*2).equals("11")) in_ext2[i+4]="3";
   }
   }

   }catch (Exception ex) {}
   }

   //ext3
   if (row_board3.length()>=8)
   {
   try {
   state=hexToBin(row_board3.substring(0,2));
           state=Bin_8bits(state);
           String board_type=state.substring(6,8);
   String input_2_zone=state.substring(2,6);

   //outputs state
   state=hexToBin(row_board3.substring(6,8));
           state=Bin_8bits(state);
   for (int i=0; i<8; i++){
   if ( (board_type.equals("00") && (i < 4)) || board_type.equals("01") )
   {
   out_ext3[i]=state.substring(7-i,8-i);
   }
   }

   //input1..4 state
   state=hexToBin(row_board3.substring(4,6));
           state=Bin_8bits(state);
   for (int i=0; i<4; i++){
   if ( board_type.equals("00") || board_type.equals("10") )
   {
   if (state.substring(6-i*2,8-i*2).equals("00")) in_ext3[i]="0";
   if (state.substring(6-i*2,8-i*2).equals("01")) in_ext3[i]="1";
   if (state.substring(6-i*2,8-i*2).equals("10")) in_ext3[i]="2";
   if (state.substring(6-i*2,8-i*2).equals("11")) in_ext3[i]="3";
   }
   }

   //input5..8 state
   state=hexToBin(row_board3.substring(2,4));
           state=Bin_8bits(state);
   for (int i=0; i<4; i++){
   if ( (board_type.equals("00") && input_2_zone.substring(3-i, 4-i).equals("1")) || board_type.equals("10") )
   {
   if (state.substring(6-i*2,8-i*2).equals("00")) in_ext3[i+4]="0";
   if (state.substring(6-i*2,8-i*2).equals("01")) in_ext3[i+4]="1";
   if (state.substring(6-i*2,8-i*2).equals("10")) in_ext3[i+4]="2";
   if (state.substring(6-i*2,8-i*2).equals("11")) in_ext3[i+4]="3";
   }
   }

   }catch (Exception ex) {}
   }

   //ext4
   if (row_board4.length()>=8)
   {
   try {
   state=hexToBin(row_board4.substring(0,2));
           state=Bin_8bits(state);
           String board_type=state.substring(6,8);
   String input_2_zone=state.substring(2,6);

   //outputs state
   state=hexToBin(row_board4.substring(6,8));
           state=Bin_8bits(state);
   for (int i=0; i<8; i++){
   if ( (board_type.equals("00") && (i < 4)) || board_type.equals("01") )
   {
   out_ext4[i]=state.substring(7-i,8-i);
   }
   }

   //input1..4 state
   state=hexToBin(row_board4.substring(4,6));
           state=Bin_8bits(state);
   for (int i=0; i<4; i++){
   if ( board_type.equals("00") || board_type.equals("10") )
   {
   if (state.substring(6-i*2,8-i*2).equals("00")) in_ext4[i]="0";
   if (state.substring(6-i*2,8-i*2).equals("01")) in_ext4[i]="1";
   if (state.substring(6-i*2,8-i*2).equals("10")) in_ext4[i]="2";
   if (state.substring(6-i*2,8-i*2).equals("11")) in_ext4[i]="3";
   }
   }

   //input5..8 state
   state=hexToBin(row_board4.substring(2,4));
           state=Bin_8bits(state);
   for (int i=0; i<4; i++){
   if ( (board_type.equals("00") && input_2_zone.substring(3-i, 4-i).equals("1")) || board_type.equals("10") )
   {
   if (state.substring(6-i*2,8-i*2).equals("00")) in_ext4[i+4]="0";
   if (state.substring(6-i*2,8-i*2).equals("01")) in_ext4[i+4]="1";
   if (state.substring(6-i*2,8-i*2).equals("10")) in_ext4[i+4]="2";
   if (state.substring(6-i*2,8-i*2).equals("11")) in_ext4[i+4]="3";
   }
   }

   }catch (Exception ex) {}
   }
